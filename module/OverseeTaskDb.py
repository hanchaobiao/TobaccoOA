import os
import datetime

from urllib import parse

from resources.base import BaseDb
from settings import MEDIA_PREFIX


class OverseeTaskModel(BaseDb):
    """
    督办任务
    """

    def __init__(self):
        BaseDb.__init__(self)
        self.yesterday = datetime.date.today() - datetime.timedelta(1)
        self.departments = []

    def get_task_detail_and_task_name_by_id(self, task_detail_id):
        """
        获取子任务详情和主任务名称
        :param task_detail_id:
        :return:
        """
        sql = "SELECT oversee_task.name, oversee_task.oversee_id, oversee_task.progress, oversee_task.completion_time," \
              " oversee_task_detail.* " \
              "FROM oversee_task JOIN oversee_task_detail ON oversee_task.id=oversee_task_detail.task_id " \
              "WHERE oversee_task_detail.id=%s"
        self.dict_cur.execute(sql, task_detail_id)
        result = self.dict_cur.fetchone()
        return result

    def get_oversee_task_detail(self, task_id):
        """
        获取任务详情
        :param task_id:
        :return:
        """
        sql = "SELECT progress FROM oversee_task WHERE id=%s"
        self.dict_cur.execute(sql, task_id)
        task = self.dict_cur.fetchone()

        sql = "SELECT sys_file_manage.* FROM rel_task_file " \
              "JOIN sys_file_manage ON rel_task_file.file_id=sys_file_manage.id WHERE task_id=%s"
        self.dict_cur.execute(sql, task_id)
        file_list = self.dict_cur.fetchall()
        task['files'] = []
        for item in file_list:
            item['url'] = parse.urljoin(MEDIA_PREFIX, item['file_path'])
            task['files'].append(item)
        sql = "SELECT detail.*, sys_admin.real_name as agent_name, dict_department.name asdepartment_name " \
              "FROM oversee_task_detail detail JOIN sys_admin " \
              "ON detail.agent_id=sys_admin.id JOIN dict_department ON detail.department_id=dict_department.id " \
              "WHERE detail.task_id=%s"
        self.dict_cur.execute(sql, task_id)
        task_detail_list = self.dict_cur.fetchall()
        sql = "SELECT rel_task_coordinator.*, sys_admin.real_name as coordinator_name FROM rel_task_coordinator " \
              "JOIN sys_admin ON coordinator_id=sys_admin.id WHERE task_id=%s"
        self.dict_cur.execute(sql, task_id)
        coordinator_list = self.dict_cur.fetchall()
        sql = "SELECT * FROM oversee_task_detail_file WHERE task_id=%s"
        self.dict_cur.execute(sql, task_id)
        file_list = self.dict_cur.fetchall()
        print(file_list)
        for task_detail in task_detail_list:
            task_detail['coordinators'] = [item for item in coordinator_list
                                           if item['task_detail_id'] == task_detail['id']]
            task_detail['files'] = []
            for item in file_list:
                if item['task_detail_id'] == task_detail['id']:
                    item['url'] = parse.urljoin(MEDIA_PREFIX, item['file_path'])
                    task_detail['files'].append(item)
        task['task_detail_list'] = task_detail_list
        return task

    def get_oversee_task_list(self, admin, name, task_type, relation, page, page_size):
        """
        任务列表
        :param admin:
        :param name:
        :param task_type:
        :param relation:
        :param page:
        :param page_size:
        :return:
        """
        sql = """
        SELECT oversee_task.*, GROUP_CONCAT(oversee_task_detail.agent_id) as agent_ids, 
            GROUP_CONCAT(rel_task_coordinator.coordinator_id ) as coordinator_ids 
        FROM oversee_task LEFT JOIN oversee_task_detail ON oversee_task.id=oversee_task_detail.task_id
        LEFT JOIN rel_task_coordinator ON oversee_task_detail.id=rel_task_coordinator.task_detail_id
        """
        conditions = []
        if admin['role_id'] == 3:
            conditions.append(" oversee_task.oversee_id={} ".format(admin['id']))
        elif admin['role_id'] == 4:
            conditions.append(" oversee_task_detail.agent_id={} ".format(admin['id']))
        if name:
            conditions.append("oversee_task.name like '%{}%'".format(name))
        if task_type:
            conditions.append("oversee_task.type='{}'".format(task_type))
        if relation == '由我发布':
            conditions.append("oversee_task.release_id={}".format(admin['id']))
        elif relation == '由我督办':
            conditions.append("oversee_task.oversee_id={}".format(admin['id']))
        elif relation == '由我经办':
            conditions.append("oversee_task_detail.agent_id={}".format(admin['id']))
        elif relation == '由我协办':
            conditions.append("rel_task_coordinator.coordinator_id={}".format(admin['id']))
        sql = self.append_query_conditions(sql, conditions)
        sql += " GROUP BY oversee_task.id"
        result = self.query_paginate(sql, sort=['add_time', 'DESC'], page=page, page_size=page_size)
        if relation == '由我经办' or relation == '由我协办':  # 补气人员
            task_ids = [res['id'] for res in result['list']]
            if len(task_ids) == 0:
                return result
            task_ids = str(tuple(task_ids)).replace(",)", ")")
            sql = "SELECT task_id, GROUP_CONCAT(agent_id) AS agent_ids FROM " \
                  "oversee_task_detail WHERE task_id IN %s GROUP BY task_id" % task_ids
            self.dict_cur.execute(sql)
            rows = self.dict_cur.fetchall()
            agent_dict = {row['task_id']: row['agent_ids'] for row in rows}
            sql = "SELECT task_id, GROUP_CONCAT(coordinator_id) AS coordinator_ids FROM " \
                  "rel_task_coordinator WHERE task_id IN %s GROUP BY task_id" % task_ids
            self.dict_cur.execute(sql)
            rows = self.dict_cur.fetchall()
            coordinator_dict = {row['task_id']: row['coordinator_ids'] for row in rows}
            for res in result['list']:
                res['agent_ids'] = agent_dict.get(res['id'])
                res['coordinator_ids'] = coordinator_dict.get(res['id'])
        return result

    @staticmethod
    def get_all_people_ids(data_list):
        """
        获取数据中人的id
        :param data_list:
        :return:
        """
        people_ids = []
        for res in data_list:
            people_ids.append(res['oversee_id'])
            people_ids.append(res['release_id'])
            if res['agent_ids']:
                people_ids.extend(res['agent_ids'].split(","))
            if res['coordinator_ids']:
                people_ids.extend(res['coordinator_ids'].split(","))
        people_ids = str(tuple(set(people_ids))).replace(",)", ")")
        return people_ids

    @staticmethod
    def convert_real_name(data_list, peoples):
        people_dict = {int(item['id']): item['real_name'] for item in peoples}
        for res in data_list:
            res['agents'] = []
            res['coordinators'] = []
            res['oversee_name'] = people_dict.get(res['oversee_id'])
            res['release_name'] = people_dict.get(res['release_id'])
            if res['agent_ids']:
                for agent_id in list(set(res['agent_ids'].split(","))):
                    res['agents'].append({"id": agent_id, "name": people_dict.get(int(agent_id))})
            if res['coordinator_ids']:
                for coordinator_id in list(set(res['coordinator_ids'].split(","))):
                    res['coordinators'].append({"id": coordinator_id, "name": people_dict.get(int(coordinator_id))})
        return data_list

    def update_oversee_task(self, task):
        """
        添加督办任务（主任务）
        :param task: 任务
        :return:
        """
        task['file_names'] = str(task['file_names'])
        self.execute_insert('oversee_task', **task)
        task['id'] = self.dict_cur.lastrowid
        return task

    def add_oversee_task_detail(self, task_id, task_detail):
        """
        添加督办任务（子任务）
        :param task_id: 主任务id
        :param task_detail: 子任务
        :return:
        """
        task_detail['status'] = '待签收'
        task_detail['task_id'] = task_id
        sql = "INSERT INTO {}({}) VALUES({})"
        self.execute_insert('oversee_task_detail', **task_detail)
        task_detail['id'] = self.dict_cur.lastrowid
        return task_detail

    def add_task_coordinator(self, task_id, task_detail_id, coordinator_id):
        """
        添加协作人（子任务）
        :param task_id: 主任务id
        :param task_detail_id: 子任务
        :param coordinator_id: 子任务
        :return:
        """
        coordinator = {"task_id": task_id, "task_detail_id": task_detail_id, "coordinator_id": coordinator_id}
        sql = "INSERT INTO {}({}) VALUES({})"
        self.execute_insert('rel_task_coordinator', **coordinator)
        coordinator['id'] = self.dict_cur.lastrowid
        return coordinator

    def delete_task(self, task_id):
        """
        删除任务
        :param task_id:
        :return:
        """
        sql = "SELECT COUNT(*) AS num FROM oversee_task_detail WHERE task_id=%s AND status='任务完成'"
        self.dict_cur.execute(sql, task_id)
        count = self.dict_cur.fetchone()['num']
        if count > 0:
            return {"code": 1, "message": "任务已完成一部分，不能删除"}
        sql = "DELETE FROM rel_task_coordinator WHERE task_id=%s"
        self.dict_cur.execute(sql, task_id)
        sql = "DELETE FROM oversee_task_detail WHERE task_id=%s"
        self.dict_cur.execute(sql, task_id)
        sql = "DELETE FROM oversee_task WHERE id=%s"
        self.dict_cur.execute(sql, task_id)
        return {"code": 0, "message": "删除成功"}

    def before_task_complete_situation(self, task_detail):
        """
        该子任务之前任务完成情况，和该任务序号
        :param task_detail:
        :return:
        """
        sql = "SELECT IFNULL(SUM(IF(status!=%s, 1, 0)), 0) AS unfinished_num, " \
              "COUNT(*) AS `index` FROM oversee_task_detail WHERE task_id=%s AND end_time < %s"
        self.dict_cur.execute(sql, ('任务完成', task_detail['task_id'], task_detail['end_time']))
        result = self.dict_cur.fetchone()
        result['index'] += 1
        return result

    def delete_file_by_ids(self, task_detail_id, ids):
        """
        删除文件
        :param task_detail_id:
        :param ids:
        :return:
        """
        if len(ids) == 0:
            return 0
        ids = str(tuple(ids)).replace(",)", ")")
        sql = "DELETE FROM oversee_task_detail_file WHERE task_detail_id=%s AND id not in %s" % (task_detail_id, ids)
        self.dict_cur.execute(sql)

    def update_task_progress(self, task_id):
        """
        修改任务进度
        :param task_id:
        :return:
        """
        sql = """UPDATE oversee_task as task, 
            (SELECT task_id, CAST(IFNULL(SUM(IF(`status`='任务完成',1,0)), 0)/COUNT(*)*100 AS SIGNED) AS progress,
             MAX(audit_time) as completion_time  FROM oversee_task_detail WHERE task_id=%s GROUP BY task_id) as detail
            SET task.progress=detail.progress, task.completion_time=IF(detail.progress=100,detail.completion_time,NULL)
            WHERE detail.task_id=task.id AND task.id=%s
            """
        print(sql)
        self.dict_cur.execute(sql, (task_id, task_id))

    def get_oversee_message_list(self, admin, only_unread, page, page_size):
        """
        获取督办类型
        :param admin:
        :param only_unread:
        :param page:
        :param page_size:
        :return:
        """
        sql = "SELECT * FROM oversee_message WHERE receive_id=%s" % admin['id']
        if only_unread:
            sql += " WHERE receive_time IS NULL "
        result = self.query_paginate(sql, sort=['send_time', 'desc'], page=page, page_size=page_size)
        return result

    def reset_rel_task_file(self, task_id, file_ids):
        """
        重置任务文件
        :param task_id:
        :param file_ids:
        :return:
        """
        sql = "DELETE FROM rel_task_file WHERE task_id={}".format(task_id)
        if len(file_ids):
            sql += " AND file_id NOT IN %s" % (str(tuple(file_ids)).replace(",)", ")"))
        self.dict_cur.execute(sql)
        if len(file_ids):
            sql = f"INSERT IGNORE INTO rel_task_file(task_id, file_id) VALUES({task_id}, %s)"
            self.dict_cur.executemany(sql, file_ids)


if __name__ == "__main__":
    am = OverseeTaskModel()
