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
        result = {'work_state': [], 'job_type': []}
        if department_id:
            sql = "SELECT status, COUNT(sys_admin.id) as num FROM sys_admin " \
                  "JOIN dict_department ON sys_admin.department_id=dict_department.id " \
                  "WHERE (department_id={pid} or path like '{pid},%' or path like '%,{pid},%' or path like '%,{pid}') " \
                  "AND sys_admin.is_delete=0 GROUP BY status".format(pid=department_id)
        else:
            sql = "SELECT status, COUNT(id) as num FROM sys_admin WHERE is_delete=0 %s GROUP BY status"
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        sum_num = 0
        for row in rows:
            if '在岗' in row['status']:
                result['job_type'].append(row)
                sum_num += row['num']
            else:
                result['work_state'].append(row)
        result['work_state'].append({"status": "在岗", "num": sum_num})
        return result

    def get_leader_statistics(self, department_id):
        """
        部门领导统计
        :param department_id:
        :return:
        """
        if department_id:
            sql = """
            SELECT position as name, COUNT(sys_admin.id) as value FROM sys_admin JOIN dict_department ON sys_admin.department_id=dict_department.id
            WHERE position NOT IN ('局长', '局领导') AND sys_admin.is_delete=0
            AND (department_id={pid} or path like '{pid},%' or path like '%,{pid},%' or path like '%,{pid}')
            GROUP BY position
            """.format(pid=department_id)
        else:
            sql = " SELECT position as name, COUNT(id) as value FROM sys_admin WHERE position NOT IN ('局长', '局领导') GROUP BY position"
        self.dict_cur.execute(sql)
        rows = self.dict_cur.fetchall()
        section_chief = []
        gj = []
        for row in rows:
            if row['name'] in ['科长', '经理', '主任', '主任科员', '副科长', '副经理', '副主任科员', '副主任']:
                section_chief.append(row)
            elif row['name'] in ['正股', '副股', '普通员工']:
                gj.append(row)
        return {"section_chief": section_chief, "gj": gj}

    def oversee_task_statistics(self, department_id):
        """
        督办任务完成情况统计
        :param department_id:
        :return:
        """
        sql = """
            SELECT status as name, COUNT(*) as value FROM (
                SELECT task_id, CASE WHEN group_concat(status) = '任务完成' then '已完成' 
                    WHEN group_concat(status) != '任务完成' AND max(end_time)<NOW() THEN '未完成'
                    ELSE '进行中' END  as status 
                FROM oversee_task_detail %s GROUP BY task_id
            ) AS tmp GROUP BY status"""
        if department_id:
            child_ids = DepartmentModel().get_child_department_by_ids(department_id)
            if child_ids:
                sql = sql % " WHERE department_id IN {}".format(str(tuple(child_ids)).replace(",)", ")"))
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
                SELECT task_id, CASE WHEN group_concat(status) = '任务完成' then '已完成' 
                    WHEN group_concat(status) != '任务完成' AND max(end_time)<NOW() THEN '未完成'
                    ELSE '进行中' END  as status 
                FROM oversee_task_detail {} GROUP BY task_id
            ) AS tmp ON oversee_task.id=tmp.task_id 
            WHERE DATE_FORMAT(add_time, '%Y-%m')>DATE_FORMAT(date_sub(curdate(), interval 12 month), '%Y-%m')
            GROUP BY month, tmp.status"""

        if department_id:
            child_ids = DepartmentModel().get_child_department_by_ids(department_id)
            if child_ids:
                sql = sql.format(" WHERE department_id IN {}".format(str(tuple(child_ids)).replace(",)", ")")))
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

    def department_oversee_task_complete_num_sort(self, department_id):
        """
        部门完成数排名
        :return:
        """
        sql = """
        SELECT * FROM oversee_task JOIN oversee_task_detail ON oversee_task.id=oversee_task_detail.task_id JOIN 
        WHERE progress=100 JOIN dict_department ON oversee_task_detail.department_id=dict_department.id 
        """

    def get_newest_tax(self):
        """
        完成税率
        :return:
        """
        sql = "SELECT * FROM tax_progress order by year desc limit 1"
        self.dict_cur.execute(sql)
        row = self.dict_cur.fetchone()
        return row or {}


if __name__ == "__main__":
    am = ReportModel()
    print(am.get_employee_status(2))
    print(am.get_leader_statistics(2))
    print(am.oversee_task_statistics(3))
    print(am.get_newest_tax())
    print(am.oversee_task_trend(None))