import numpy as np
import pandas as pd
# 导入初始数据

from resources.base import BaseDb


def load_department():
    path = "../../media/襄阳烟草市局员工名单.xls"
    df = pd.read_excel(path, skiprows=[0])
    dws = list(set(np.array(df['单位']).tolist()))
    print(dws)
    model = BaseDb()

    sql = "INSERT IGNORE INTO dict_department(name, level, pid) value (%s, 1, null)"
    model.dict_cur.executemany(sql, dws)
    model.conn.commit()

    bms = list(set(np.array(df['部门']).tolist()))
    sql = "INSERT IGNORE INTO dict_department(name, level, pid) value (%s, 2, 1)"
    model.dict_cur.executemany(sql, bms)
    model.conn.commit()

    for index, row in df.iterrows():
        password = "46f94c8de14fb36680850768ff1b7f2a"
        sql = "INSERT INTO sys_admin(id, username, password, real_name, phone, sex, position, department_id, " \
              "is_disable, add_time) value (UUID(), %s, %s, %s, %s, null, null, %s, false, now())"
        model.dict_cur.execute(sql, (row['用户名'], password, row['姓名'], ))


if __name__ == '__main__':
    load_department()
