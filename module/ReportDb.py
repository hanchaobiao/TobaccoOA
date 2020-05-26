import datetime
from copy import deepcopy

from urllib import parse
from dateutil.relativedelta import relativedelta

from resources.base import BaseDb
from module.DepartmentDb import DepartmentModel
from settings import MEDIA_PREFIX


class ReportModel(BaseDb):
    """
    大屏统计
    """

    def __init__(self):
        BaseDb.__init__(self)

    def get_employee_status(self, department_id):
        """
        统计员工状态
        :param department_id:
        :return:
        """

        result = {'work_state': [{"status": "退岗", "num": 0}, {"status": "内退", "num": 0},
                                 {"status": "退休", "num": 0}, {"status": "改非", "num": 0}],
                  'job_type': [{"status": '在岗正式工', "num": 0},
                               {"status": '在岗人事代理', "num": 0},
                               {"status": '在岗劳务派遣', "num": 0}]}
        sql = "SELECT status, COUNT(id) as num FROM sys_admin WHERE is_delete=0 {} GROUP BY status"
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql.format(" AND department_id IN %s " % (str(tuple(child_dict.keys())).replace(",)", ")")))
        else:
            sql = sql.format('')
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        sum_num = 0
        for row in rows:
            for item in result['work_state']:
                if row['status'] == item['status']:
                    item['num'] = row['num']
            for item in result['job_type']:
                if row['status'] == item['status']:
                    item['num'] = row['num']
            if '在岗' in row['status']:
                sum_num += row['num']
        result['work_state'].append({"status": "在岗", "num": sum_num})
        return result

    def get_leader_statistics(self, department_id):
        """
        部门领导统计
        :param department_id:
        :return:
        """
        sql = " SELECT position as name, COUNT(id) as value FROM sys_admin " \
              " WHERE position NOT IN ('局长', '局领导') {} GROUP BY position"
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql.format(" AND department_id IN %s " % (str(tuple(child_dict.keys())).replace(",)", ")")))
        else:
            sql = sql.format('')
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        all_section_name = ['科长', '经理', '主任', '主任科员', '副科长', '副经理', '副主任科员', '副主任']
        section_chief = []
        section_chief_names = set()
        all_gj_name = ['正股', '副股', '普通员工']
        gj = []
        gj_names = []
        for row in rows:
            if row['name'] in all_section_name:
                section_chief.append(row)
                section_chief_names.add(row['name'])
            elif row['name'] in all_gj_name:
                gj.append(row)
                gj_names.append(row['name'])
        for name in all_section_name:
            if name not in section_chief_names:
                section_chief.append({"name": name, "value": 0})
        for name in all_gj_name:
            if name not in gj_names:
                gj.append({"name": name, "value": 0})
        return {"section_chief": section_chief, "gj": gj}

    def oversee_task_statistics(self, department_id):
        """
        督办任务完成情况统计
        :param department_id:
        :return:
        """
        sql = """
            SELECT status as name, COUNT(*) as value FROM (
                SELECT task_id, CASE WHEN group_concat(DISTINCT status) = '任务完成' then '已完成' 
                    WHEN group_concat(DISTINCT status) != '任务完成' AND max(end_time)<NOW() THEN '未完成'
                    ELSE '进行中' END  as status 
                FROM oversee_task_detail %s GROUP BY task_id
            ) AS tmp GROUP BY status"""
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql % " WHERE department_id IN {}".format(str(tuple(child_dict.keys())).replace(",)", ")"))
        else:
            sql = sql % ''
        self.dict_cur.execute(sql)
        rows = list(self.dict_cur.fetchall())
        status_list = [row['name'] for row in rows]
        for state in ['已完成', '未完成', '进行中']:
            if state not in status_list:
                rows.append({"name": state, "value": 0})
        return rows

    def oversee_task_trend(self, department_id):
        """
        督办任务趋势，近12个月
        :param department_id:
        :return:
        """
        sql = """
            SELECT DATE_FORMAT(add_time, '%Y-%m') as month, tmp.status as name, COUNT(*) as value 
            FROM oversee_task JOIN (
                SELECT task_id, CASE WHEN group_concat(DISTINCT status) = '任务完成' then '已完成' 
                    WHEN group_concat(DISTINCT status) != '任务完成' AND max(end_time)<NOW() THEN '未完成'
                    ELSE '进行中' END  as status 
                FROM oversee_task_detail {} GROUP BY task_id
            ) AS tmp ON oversee_task.id=tmp.task_id 
            WHERE DATE_FORMAT(add_time, '%Y-%m')>DATE_FORMAT(date_sub(curdate(), interval 12 month), '%Y-%m')
            GROUP BY month, tmp.status"""

        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql.format(" WHERE department_id IN {}".format(str(tuple(child_dict.keys())).replace(",)", ")")))
        else:
            sql = sql.format('')
        self.dict_cur.execute(sql)
        rows = list(self.dict_cur.fetchall())
        start_month = datetime.datetime.now() - relativedelta(months=11)
        axis = [(start_month+relativedelta(months=i)).strftime('%Y-%m') for i in range(12)]
        default_val = [0 for _ in range(12)]
        data_dict = {"发布数": deepcopy(default_val), "已完成": deepcopy(default_val),
                     "进行中": deepcopy(default_val), "未完成": deepcopy(default_val)}
        for row in rows:
            index = axis.index(row['month'])
            data_dict[row['name']][index] = row['value']
        for i in range(len(data_dict['发布数'])):
            data_dict['发布数'][i] = data_dict['已完成'][i] + data_dict['进行中'][i] + data_dict['未完成'][i]
        data_list = []
        for name, data in data_dict.items():
            data_list.append({"name": name, "data": data})
        return {"x_axis": axis, "y_axis": data_list}

    def get_newest_tax(self):
        """
        完成税率
        :return:
        """
        sql = "SELECT * FROM tax_progress order by year desc limit 10"
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        return rows

    def department_oversee_task_complete_num_sort(self, department_id=2):
        """
        部门完成数排名
        :return:
        """
        # sql = """
        # SELECT department_id, dict_department.name, `type`, status, COUNT(1) as num FROM (
        #     SELECT oversee_task.id, d.department_id, `type`,
        #         CASE WHEN group_concat(DISTINCT d.status)='任务完成' then '已完成'
        #         WHEN group_concat(DISTINCT d.status) != '任务完成' AND max(end_time)<NOW() THEN '未完成'
        #         ELSE '进行中' END  as status
        #     FROM oversee_task JOIN oversee_task_detail d ON oversee_task.id=d.task_id {}
        #     GROUP BY oversee_task.id, d.department_id, `type`, d.status HAVING group_concat(DISTINCT d.status)='任务完成'
        # ) AS tmp JOIN dict_department ON tmp.department_id=dict_department.id
        # GROUP BY department_id, dict_department.name, `type`, status
        # """
        sql = """
              SELECT department_id as id, dict_department.name, `type`, 
                COUNT(task_num) as task_num, COUNT(complete_num) as complete_num FROM (
                  SELECT oversee_task.id, d.department_id, `type`, 
                    1 AS task_num, IF(group_concat(DISTINCT d.status)='任务完成', 1, NULL) as complete_num
                    FROM oversee_task JOIN oversee_task_detail d ON oversee_task.id=d.task_id {} 
                    GROUP BY oversee_task.id, d.department_id, `type`
                ) AS tmp JOIN dict_department ON tmp.department_id=dict_department.id GROUP BY department_id, dict_department.name, `type`
                """
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql.format(" WHERE d.department_id IN %s " % (str(tuple(child_dict.keys())).replace(",)", ")")))
        else:
            sql = sql.format('')
        self.dict_cur.execute(sql)
        rows = list(self.dict_cur.fetchall())
        oversee_type_dict = {"专项事务": {"total": {"task_num": 0, "complete_num": 0}, "list": []},
                             "重大事务": {"total": {"task_num": 0, "complete_num": 0}, "list": []},
                             "紧急事务": {"total": {"task_num": 0, "complete_num": 0}, "list": []},
                             "常规事务": {"total": {"task_num": 0, "complete_num": 0}, "list": []}}
        for row in rows:
            oversee_type_dict[row['type']]['list'].append(row)
            oversee_type_dict[row['type']]['total']['task_num'] += row['task_num']
            oversee_type_dict[row['type']]['total']['complete_num'] += row['complete_num']
        for task_type, data in oversee_type_dict.items():
            ids = [row['id'] for row in data['list']]
            diff_ids = list(set(child_dict.keys()).difference(set(ids)))
            for department_id in diff_ids:
                child_dict[department_id]['complete_num'] = 0
                child_dict[department_id]['task_num'] = 0
                data['list'].append(child_dict[department_id])
            rows.sort(key=lambda x: (x['complete_num'], x['complete_num']/(x['task_num'] or 1), -x['id']), reverse=True)
        return oversee_type_dict


if __name__ == "__main__":
    am = ReportModel()
    print(am.get_employee_status(2))
    print(am.get_leader_statistics(2))
    print(am.oversee_task_statistics(3))
    print(am.get_newest_tax())
    print(am.oversee_task_trend(None))
    print(am.department_oversee_task_complete_num_sort())
