# import os
# import datetime
# from io import BytesIO
#
# import xlwt
# import xlrd
# from xlutils.copy import copy
# import numpy as np
# import pandas as pd
# import pymysql
# from docx.shared import Pt
# from docx.oxml.ns import qn
# from docx import Document
# from docx.enum.table import WD_TABLE_ALIGNMENT
#
# from resources.base import BaseDb
# from module import convert_columns
# from settings import BASE_DIR
#
#
# class EmployeeModel(BaseDb):
#     """
#     优惠券计算模型
#     """
#
#     def __init__(self):
#         BaseDb.__init__(self)
#         self.yesterday = datetime.date.today() - datetime.timedelta(1)
#
#     def get_employee_list(self, nickname, organization, page, page_size):
#         """
#         员工列表
#         :param nickname:
#         :param organization:
#         :param page:
#         :param page_size:
#         :return:
#         """
#         columns = list(convert_columns.values())
#         columns.insert(0, 'id')
#         sql = "SELECT {} FROM employee".format(','.join(columns))
#         query = []
#         if nickname:
#             query.append(" nickname like '%{}%'".format(nickname))
#         if organization:
#             query.append(" organization like '%{}%'".format(organization))
#         if len(query):
#             sql += " WHERE " + " AND ".join(query)
#
#         sql_count = sql.replace(','.join(columns), ' count(*) as num ')
#         self.dic_cur.execute(sql_count)
#         count = self.dic_cur.fetchone()['num']
#         sql += " LIMIT {}, {}".format((page-1)*page_size, page_size)
#         self.dic_cur.execute(sql)
#         return {"count": count, "list": self.dic_cur.fetchall()}
#
#     def add_employee(self, employee):
#         """
#         添加员工
#         :param employee:
#         :return:
#         """
#         cols = list(convert_columns.values())
#         columns = []
#         values = []
#         for key, val in employee.items():
#             if key in cols:
#                 columns.append(key)
#                 values.append(val)
#         try:
#             sql = "INSERT INTO employee({}) VALUES({})".format(','.join(columns),
#                                                                ','.join(['%s' for _ in range(len(columns))]))
#             self.dic_cur.execute(sql, tuple(values))
#             self.conn.commit()
#             return {"message": "员工信息录入成功"}
#         except pymysql.err.IntegrityError:
#             return {"code": "FAIL", "message": "该用户已存在"}
#
#     def update_employee(self, admin, employee):
#         """
#         修改员工
#         :param admin:
#         :param employee:
#         :return:
#         """
#
#         cols = list(convert_columns.values())
#         columns = []
#         values = []
#         for key, val in employee.items():
#             if key in cols:
#                 columns.append(key)
#                 values.append(val)
#         try:
#             update = ','.join(['`{}`="{}"'.format(key, val) for key, val in employee.items() if key in cols])
#             sql = "UPDATE employee SET {} WHERE id={}".format(update, employee['id'])
#             if admin['role_name'] != "超级管理员":
#                 sql += " AND organization='{}' ".format(admin['organization'])
#             self.dic_cur.execute(sql)
#             self.conn.commit()
#             return {"message": "员工信息修改成功"}
#         except pymysql.err.IntegrityError:
#             return {"code": "FAIL", "message": "员工已存在"}
#
#     def delete_employee(self, admin, ids):
#         """
#         删除员工
#         :param admin:
#         :param ids:
#         :return:
#         """
#         sql = "DELETE FROM employee WHERE id in ({})".format(','.join([str(_id) for _id in ids]))
#         if admin['role_name'] != "超级管理员":
#             sql += " AND organization='{}' ".format(admin['organization'])
#         count = self.dic_cur.execute(sql)
#         self.conn.commit()
#         return {"message": "成功删除{}条信息".format(count)}
#
#     def load_employee_excel_data(self, admin, stream):
#         """
#         导入excel数据
#         :return:
#         """
#         df = pd.read_excel(stream, index=False, header=2, skiprows=(3, ), skip_footer=3)
#         df = df.reset_index()
#         try:
#             columns = list(convert_columns.keys())
#             columns.remove("年龄")
#             columns.remove("行业工作年限")
#             # filter_cols = []
#             # for col in df.columns:
#             #     if col in columns:
#             #         filter_cols.append(col)
#             df = df[columns]
#             if admin['role_name'] != "超级管理员":
#                 if len(df[df.organization != admin['organization']]) > 0:
#                     return {"code": "FAIL", "message": "文件中存在非本部门员工，请检查是否填写有误"}
#         except KeyError:
#             import traceback
#             traceback.print_exc()
#             return {"code": "FAIL", "message": "excel数据格式错误"}
#         df = df.rename(columns=convert_columns)
#         columns = list(df.columns)
#         columns_str = ','.join(list(df.columns))
#         value = ','.join(["%s" for _ in columns])
#         update = ','.join(["{}=%s".format(col) for col in columns])
#         sql = "INSERT INTO employee({}) values ({})  ON DUPLICATE KEY UPDATE {}".format(columns_str, value, update)
#         df = df[(pd.isnull(df.nickname)) | (df.nickname == "") == False]
#         df = df.fillna("")
#         data_list = np.array(df).tolist()
#         for data in data_list:
#             for index, d in enumerate(data):
#                 if d == '':
#                     data[index] = None
#         data_list = [tuple(data*2) for data in data_list]
#         for data in data_list:
#             self.dic_cur.execute(sql, data)
#         self.conn.commit()
#         return {"message": "数据导入成功"}
#
#     def export_employee_list(self, nickname, organization):
#         """
#         员工列表
#         :param nickname:
#         :param organization:
#         :return:
#         """
#         columns = list(convert_columns.values())
#         sql = "SELECT {} FROM employee".format(','.join(columns))
#         query = []
#         if nickname:
#             query.append(" nickname like '%{}%'".format(nickname))
#         if organization:
#             query.append(" organization like '%{}%'".format(organization))
#         if len(query):
#             sql += " WHERE " + " AND ".join(query)
#         self.dic_cur.execute(sql)
#         rows = self.dic_cur.fetchall()
#         return self.export_excel(rows)
#
#     @staticmethod
#     def export_excel(rows):
#         from settings import BASE_DIR
#         path = os.path.join(BASE_DIR, "media/excel/员工信息模板.xls")
#         data = xlrd.open_workbook(path, formatting_info=True)
#         excel = copy(wb=data)  # 完成xlrd对象向xlwt对象转换
#         excel_table = excel.get_sheet(0)  # 获得要操作的页
#         style = xlwt.XFStyle()  # 初始化样式
#         font = xlwt.Font()  # 为样式创建字体
#         font.name = u'宋体'
#         font.bold = True  # 黑体
#         font.underline = False  # 下划线
#         font.italic = False  # 斜体字
#         style.font = font  # 设定样式
#
#         al = xlwt.Alignment()
#         al.horz = 0x02  # 设置水平居中
#         al.vert = 0x01  # 设置垂直居中
#         style.alignment = al
#
#         # max_rows = table.nrows  # 获得行数
#         insert_row = 3
#
#         for row_index, row in enumerate(rows):
#             values = list(row.values())
#             values.insert(0, row_index+1)
#             for index, val in enumerate(values):
#                 excel_table.col(index).width = 3333
#                 excel_table.write(insert_row + 1, index, val or '', style)  # 因为单元格从0开始算，所以row不需要加一
#             insert_row = insert_row + 1
#
#         # 写出到IO
#         output = BytesIO()
#         excel.save(output)
#         # 重新定位到开始
#         return output
#
#     def get_employee_by_id(self, admin, employee_id):
#         """
#         根据Id查询员工信息
#         :param admin:
#         :param employee_id:
#         :return:
#         """
#         sql = "SELECT * FROM employee WHERE id=%s"
#         if admin['role_name'] != "超级管理员":
#             sql += " AND organization='{}'".format(admin['organization'])
#         self.dic_cur.execute(sql, employee_id)
#         row = self.dic_cur.fetchone()
#         if row:
#             row = {key: str(val).strip() if val else '' for key, val in row.items()}
#         return row
#
#     @staticmethod
#     def export_word(employee):
#         if employee is None:
#             return
#         path = os.path.join(BASE_DIR, 'media/word/员工基本情况表.docx')
#         document = Document(path)
#         document.styles['Normal'].font.name = u'宋体'
#         document.styles['Normal'].font.size = Pt(12)
#         # noinspection PyProtectedMember
#         document.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), u'宋体')
#
#         # 表格
#         table = document.tables
#         # 设置字体
#         # table_0 = table[0]
#         # table_0.style.font.name = u'宋体'
#         # table_0.style.font.size = Pt(18)  # 小四
#         # table[1].style.font.name = u'宋体'
#         # table[1].style.font.size = Pt(18)  # 小四
#         # 获取第一行的单元格列表
#         hdr_cells = table[0].rows[0].cells
#         hdr_cells[1].text = employee['nickname']
#         hdr_cells[3].text = employee['gender']
#         hdr_cells[5].text = employee['birthday']
#         for i in [1, 3, 5]:  # 居中
#             hdr_cells[i].paragraphs[0].paragraph_format.alignment = WD_TABLE_ALIGNMENT.CENTER
#         # 第二行单元格
#         hdr_cells = table[0].rows[1].cells
#         hdr_cells[1].text = employee['national']
#         hdr_cells[3].text = employee['native_place']
#         hdr_cells[5].text = employee['politics_status']
#
#         for i in [1, 3, 5]:  # 居中
#             hdr_cells[i].paragraphs[0].paragraph_format.alignment = WD_TABLE_ALIGNMENT.CENTER
#         # 第三行单元格
#         hdr_cells = table[0].rows[2].cells
#         hdr_cells[1].text = employee['entry_party_date']
#         hdr_cells[3].text = employee['party_position']
#         hdr_cells[5].text = employee['entry_tobacco_date']
#         for i in [1, 3, 5]:  # 居中
#             hdr_cells[i].paragraphs[0].paragraph_format.alignment = WD_TABLE_ALIGNMENT.CENTER
#         # 第四行单元格
#         hdr_cells = table[0].rows[3].cells
#         hdr_cells[1].text = employee['professional_qualifications'] + '\n' + employee['certificate_date']
#         hdr_cells[3].text = employee['special_skills'] + '\n' + employee['skills_certificate_date']
#         hdr_cells[5].text = employee['basic_work_month']
#         for i in [1, 3, 5]:  # 居中
#             hdr_cells[i].paragraphs[0].paragraph_format.alignment = WD_TABLE_ALIGNMENT.CENTER
#         # 第五行单元格
#         hdr_cells = table[0].rows[4].cells
#         hdr_cells[3].text = employee['first_graduation_date']
#         hdr_cells[6].text = employee['first_graduate_school'] + ' ' + employee['first_major']
#         # 第五行单元格
#         hdr_cells = table[0].rows[5].cells
#         hdr_cells[3].text = employee['master_graduation_date']
#         hdr_cells[6].text = employee['master_graduate_school'] + ' ' + employee['master_major']
#         # 第六行单元格
#         hdr_cells = table[0].rows[6].cells
#         hdr_cells[3].text = employee['work_position']
#         hdr_cells[6].text = employee['present_work_month']
#         # 第七行单元格
#         hdr_cells = table[0].rows[7].cells
#         hdr_cells[3].text = employee['work_experience']
#
#         hdr_cells = table[0].rows[8].cells
#         hdr_cells[1].text = employee['trained_experience']
#
#         hdr_cells = table[0].rows[9].cells
#
#         hdr_cells[1].text = "奖励：" + employee['winning_situation'] + '\n' + '惩罚：' + employee['punishment_situation']
#
#         hdr_cells = table[0].rows[10].cells
#         hdr_cells[1].text = employee['science_achievements']
#
#         hdr_cells = table[0].rows[11].cells
#         hdr_cells[1].text = employee['family_members']
#
#         hdr_cells = table[0].rows[12].cells
#         hdr_cells[1].text = employee['join_situation']
#
#         hdr_cells = table[0].rows[13].cells
#         hdr_cells[1].text = employee['relatives_business']
#
#         hdr_cells = table[0].rows[14].cells
#         hdr_cells[1].text = employee['industry_relatives']
#
#         document.add_page_break()
#
#         # 保存
#         output = BytesIO()
#         document.save(output)
#         # 重新定位到开始
#         return output, employee['nickname']
#
#
# if __name__ == "__main__":
#     um = EmployeeModel()
#     # um.load_employee_excel_data()
#     # print(um.get_employee_list("张三", "市局机关", 1, 10))
#     # um.add_employee({"nickname": "张三", "birthday": "1983", "party_position": "市局机关二支部宣传委员"})
#     # um.export_employee_list(nickname=None, organization=None)
#     row = um.get_employee_by_id({"role_name": "超级管理员"}, 62)
#     um.export_word(row)
