import datetime

from urllib import parse

from resources.base import BaseDb
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


if __name__ == "__main__":
    am = ReportModel()
    print(am.get_employee_status(2))
