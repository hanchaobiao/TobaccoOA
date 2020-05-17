import datetime

from resources.base import BaseDb


class DepartmentModel(BaseDb):
    """
    管理员模型
    """

    def __init__(self):
        BaseDb.__init__(self)
        self.yesterday = datetime.date.today() - datetime.timedelta(1)
        self.departments = []

    def is_exists_sub_department(self, pid):
        """
        获取子部门
        :param pid:
        :return:
        """
        sql = "SELECT COUNT(*) as num FROM dict_department WHERE pid=%s"
        self.dict_cur.execute(sql, pid)
        return self.dict_cur.fetchone()['num']

    def is_department_leader(self, user_id):
        """
        是否是部门负责人
        :param user_id:
        :return:
        """
        sql = "SELECT COUNT(*) as num FROM dict_department WHERE leader_id=%s"
        self.dict_cur.execute(sql, user_id)
        return self.dict_cur.fetchone()['num']

    def generate_department_tree(self, pid, departments):
        """
        生成菜单: 递归
        :param pid:
        :param departments:
        :return:
        """
        """
        根据传递过来的父菜单id，递归设置各层次父菜单的子菜单列表
        :param id: 父级id
        :param children: 子菜单列表
        :return: 如果这个菜单没有子菜单，返回None;如果有子菜单，返回子菜单列表
        """
        # 记录子菜单列表
        children = []
        # 遍历子菜单
        for m in departments:
            if m['pid'] == pid:
                children.append(m)

        # 把子菜单的子菜单再循环一遍
        for sub in children:
            departments2 = [item for item in self.departments if item['pid'] == pid]
            # 还有子菜单
            if len(departments):
                children_ = self.generate_department_tree(sub['id'], departments2)
                if len(children_):
                    sub['children'] = children_
        # 子菜单列表不为空
        if len(children):
            return children
        else:  # 没有子菜单了
            return []

    def get_department_tree(self, pid):
        """
        部门管理
        :param pid:
        :return:
        """
        print(pid)
        sql = " SELECT id, name, level, leader_id, pid FROM dict_department WHERE is_delete=0 "
        if pid:
            sql += " AND (id={pid} or path like '{pid},%' or path like '%,{pid},%' or path like '%,{pid}')".format(pid=pid)
        self.dict_cur.execute(sql)
        departments = self.dict_cur.fetchall()
        self.departments = departments
        root_departments = [item for item in departments if item['pid'] == pid]
        for root in root_departments:
            children = [item for item in departments if item['pid'] == root['id']]
            root['children'] = self.generate_department_tree(root['id'], children)
        return root_departments

    def get_department_by_id(self, department_id):
        """
        获取部门
        :param department_id:
        :return:
        """
        sql = "SELECT * FROM dict_department WHERE id=%s AND is_delete=0"
        self.dict_cur.execute(sql, department_id)
        department = self.dict_cur.fetchone()
        return department

    def get_department_by_name(self, name):
        """
        根据名称获取部门
        :param name:
        :return:
        """
        sql = "SELECT * FROM dict_department WHERE name=%s AND is_delete=0"
        self.dict_cur.execute(sql, name)
        department = self.dict_cur.fetchone()
        return department

    def add_department(self, department):
        """
        添加部门
        :param department:
        :return:
        """
        parent_department = self.get_department_by_id(department['pid'])
        if parent_department is None:
            return {"code": 1, "message": "上级部门不存在"}
        department['path'] = ','.join([parent_department['path'] or '', str(department['pid'])])\
            if parent_department['path'] else parent_department['id']
        department['level'] = parent_department['level'] + 1

        sql = "INSERT INTO dict_department({}) VALUES({})"
        sql = self.sql_fill_column(sql, **department)
        self.dict_cur.execute(sql, list(department.values()))
        department['id'] = self.dict_cur.lastrowid
        return department

    def update_department(self, data):
        """
        修改部门
        :param data:
        :return:
        """
        sql = "UPDATE dict_department SET name=%s, leader_id=%s WHERE id=%s"
        count = self.dict_cur.execute(sql, (data['name'], data['leader_id'], data['id']))
        return count

    def delete_department(self, department_id):
        """
        删除部门
        :param department_id:
        :return:
        """
        sql = "UPDATE dict_department SET is_delete=1 WHERE id=%s"
        count = self.dict_cur.execute(sql, department_id)
        return count


if __name__ == "__main__":
    am = DepartmentModel()
