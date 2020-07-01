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
        # for name in all_section_name:
        #     if name not in section_chief_names:
        #         section_chief.append({"name": name, "value": 0})
        # for name in all_gj_name:
        #     if name not in gj_names:
        #         gj.append({"name": name, "value": 0})
        return {"section_chief": section_chief, "gj": gj}

    def oversee_task_statistics(self, department_id):
        """
        督办任务完成情况统计
        :param department_id:
        :return:
        """
        sql = """
            SELECT status as name, COUNT(DISTINCT id) as value FROM (
                 SELECT oversee_task.id,
                        CASE WHEN oversee_task.status='任务完成' then '已完成'
                        WHEN oversee_task.status != '任务完成' AND max(end_time)<NOW() THEN '未完成'
                        ELSE '进行中' END  as status
                    FROM oversee_task JOIN oversee_task_detail d ON oversee_task.id=d.task_id %s
                    GROUP BY oversee_task.id
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
            SELECT month, tmp.status as name, COUNT(DISTINCT id) as value 
            FROM (
                SELECT DATE_FORMAT(add_time, '%Y-%m') as month, oversee_task.id,
                        CASE WHEN oversee_task.status='任务完成' then '已完成'
                        WHEN oversee_task.status != '任务完成' AND max(end_time)<NOW() THEN '未完成'
                        ELSE '进行中' END  as status
                    FROM oversee_task JOIN oversee_task_detail d ON oversee_task.id=d.task_id 
                    AND DATE_FORMAT(add_time, '%Y-%m')>DATE_FORMAT(date_sub(curdate(), interval 12 month), '%Y-%m') {}
                    GROUP BY oversee_task.id 
            ) AS tmp
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

    def oversee_type_complete_situation(self, department_id):
        """
        事务分类完成情况
        :param department_id:
        :return:
        """
        sql = """
        SELECT type, status, COUNT(DISTINCT id) AS number FROM (
            SELECT oversee_task.id, `type`,
                CASE WHEN oversee_task.status='任务完成' then 'complete_num'
                WHEN oversee_task.status != '任务完成' AND max(end_time)<NOW() THEN 'overdue_num'
                ELSE 'ongoing_num' END  as status
            FROM oversee_task JOIN oversee_task_detail d ON oversee_task.id=d.task_id {}
            GROUP BY oversee_task.id, `type`
        ) AS tmp GROUP BY `type`, status
        """
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql.format(" WHERE d.department_id IN %s " % (str(tuple(child_dict.keys())).replace(",)", ")")))
        else:
            sql = sql.format('')
        self.dict_cur.execute(sql)
        rows = list(self.dict_cur.fetchall())
        oversee_type_dict = {"专项事务": {"task_num": 0, "complete_num": 0, "ongoing_num": 0, "overdue_num": 0},
                             "重大事务": {"task_num": 0, "complete_num": 0, "ongoing_num": 0, "overdue_num": 0},
                             "紧急事务": {"task_num": 0, "complete_num": 0, "ongoing_num": 0, "overdue_num": 0},
                             "常规事务": {"task_num": 0, "complete_num": 0, "ongoing_num": 0, "overdue_num": 0}}
        for row in rows:
            oversee_type_dict[row['type']][row['status']] = row['number']
            oversee_type_dict[row['type']]['task_num'] += row['number']
        return oversee_type_dict

    def get_newest_tax(self):
        """
        完成税率
        :return:
        """
        sql = "SELECT * FROM tax_progress order by year desc limit 10"
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        return rows

    def department_oversee_task_complete_num_sort(self, department_id=2, date=None):
        """
        部门完成数排名
        :return:
        """
        internal_sql = """
            SELECT oversee_task.id, d.department_id, `type`, oversee_task.id as task_id, 
            IF(oversee_task.status='任务完成', oversee_task.id, NULL) as complete_id
            FROM oversee_task JOIN oversee_task_detail d ON oversee_task.id=d.task_id 
        """
        conditions = []
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id, include_self=False)
            if child_dict:
                conditions.append("d.department_id IN %s " % (str(tuple(child_dict.keys())).replace(",)", ")")))
        if date:
            conditions.append("DATE_FORMAT(oversee_task.add_time, '%Y-%m')='{}'".format(date))
        internal_sql = self.append_query_conditions(internal_sql, conditions)

        sql = """
              SELECT department_id as id, dict_department.name, `type`, 
                COUNT(DISTINCT task_id) as task_num, COUNT(DISTINCT complete_id) as complete_num, 
                COUNT(DISTINCT complete_id)/COUNT(DISTINCT task_id) as complete_rate FROM (
                    {}
                    GROUP BY oversee_task.id, d.department_id, `type`
                ) AS tmp JOIN dict_department ON tmp.department_id=dict_department.id 
                GROUP BY department_id, dict_department.name, `type`
                """.format(internal_sql)
        self.dict_cur.execute(sql)
        rows = list(self.dict_cur.fetchall())
        oversee_type_dict = {"专项事务": {"total": {"task_num": 0, "complete_num": 0, "complete_rate": 0}, "list": []},
                             "重大事务": {"total": {"task_num": 0, "complete_num": 0, "complete_rate": 0}, "list": []},
                             "紧急事务": {"total": {"task_num": 0, "complete_num": 0, "complete_rate": 0}, "list": []},
                             "常规事务": {"total": {"task_num": 0, "complete_num": 0, "complete_rate": 0}, "list": []}}
        for row in rows:
            oversee_type_dict[row['type']]['list'].append(row)
            oversee_type_dict[row['type']]['total']['task_num'] += row['task_num']
            oversee_type_dict[row['type']]['total']['complete_num'] += row['complete_num']
        for task_type, data in oversee_type_dict.items():
            data['total']['complete_rate'] = round(data['total']['complete_num'] / data['total']['task_num'], 4)\
                if data['total']['task_num'] else 0
            ids = [row['id'] for row in data['list']]
            diff_ids = list(set(child_dict.keys()).difference(set(ids)))
            for department_id in diff_ids:
                child_dict[department_id]['complete_num'] = 0
                child_dict[department_id]['task_num'] = 0
                child_dict[department_id]['complete_rate'] = 0
                data['list'].append(child_dict[department_id])
            rows.sort(key=lambda x: (x['complete_num'], x['complete_num']/(x['task_num'] or 1), -x['id']), reverse=True)
        return oversee_type_dict

    def unfinished_task_list(self, department_id=2):
        """
        未完成任务列表
        :param department_id:
        :return:
        """
        sql = """
        SELECT task_no, name, oversee_task.type, oversee_task_detail.department_id as agent_department_id,
          oversee_id, agent_id, DATE_FORMAT(start_time, '%Y-%m-%d') as start_time, 
          DATE_FORMAT(end_time, '%Y-%m-%d') as end_time  FROM oversee_task JOIN (
            SELECT task_id, agent_id, department_id, start_time, end_time FROM oversee_task_detail WHERE id in (
                SELECT min(id) as id FROM oversee_task_detail WHERE status != '任务完成' {} GROUP BY task_id
            )
        ) AS oversee_task_detail ON oversee_task.id=oversee_task_detail.task_id 
        """
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql.format(" AND department_id IN %s " % (str(tuple(child_dict.keys())).replace(",)", ")")))
        else:
            sql = sql.format('')
            child_dict = DepartmentModel().get_child_department_by_ids(None)
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        if len(rows) == 0:
            return []
        user_ids = set()
        for row in rows:
            user_ids.add(row['agent_id'])
            user_ids.add(row['oversee_id'])
        sql = "SELECT id, real_name FROM sys_admin WHERE id in %s" % str(tuple(user_ids)).replace(",)", ")")
        self.dict_cur.execute(sql)
        user_list = self.dict_cur.fetchall()
        user_dict = {row['id']: row['real_name'] for row in user_list}
        for row in rows:
            row['agent_department_name'] = child_dict[row['agent_department_id']]
            row['agent_name'] = user_dict[row['agent_id']]
            row['oversee_name'] = user_dict[row['oversee_id']]
        return rows

    def year_important_task(self, department_id, year, year_month):
        """
        年度重点事务
        :return:
        """
        sql = "SELECT oversee_task.name, DATE_FORMAT(oversee_task.add_time, '%Y-%m-%d') as date, " \
              "real_name as oversee_name, dict_department.name as department_name " \
              "FROM oversee_task JOIN sys_admin ON oversee_id=sys_admin.id " \
              "JOIN dict_department ON department_id=dict_department.id " \
              "WHERE oversee_task.`type`='重大事务' "
        if department_id:
            child_dict = DepartmentModel().get_child_department_by_ids(department_id)
            if child_dict:
                sql = sql.format(" AND department_id IN %s " % (str(tuple(child_dict.keys())).replace(",)", ")")))
        else:
            sql = sql.format('')

        if year:
            sql += " DATE_FORMAT(oversee_task.add_time, '%Y')='{}'".format(year)
        elif year_month:
            sql += " DATE_FORMAT(oversee_task.add_time, '%Y-%m')='{}'".format(year_month)
        sql += " ORDER BY oversee_task.add_time desc "
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        return rows

    def completed_wish_list(self):
        """
        已完成心愿，回复心愿列表
        :return:
        """
        sql = "SELECT id, name, submit_content  FROM employee_wish WHERE status='心愿完成' order by submit_time desc"
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        return rows

    def get_wish_list(self):
        """
        全部心愿列表
        :return:
        """
        sql = "SELECT id, name, wish_content, status, submit_content, submit_time, give_like_num, " \
              "DATEDIFF(submit_time, add_time) as cost_day FROM employee_wish " \
              "WHERE status = '心愿完成' order by give_like_num desc, add_time desc"
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        return {"count": len(rows), "list": rows}


if __name__ == "__main__":
    am = ReportModel()
    # print(am.get_employee_status(2))
    # print(am.get_leader_statistics(2))
    # print(am.oversee_task_statistics(3))
    # print(am.get_newest_tax())
    # print(am.oversee_task_trend(None))
    # print(am.department_oversee_task_complete_num_sort(date='2020-06'))
    # print(am.oversee_type_complete_situation(None))
    # print(am.year_important_task(''))
    print(am.unfinished_task_list())
