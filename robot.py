import pymssql

from sqlalchemy import func

from sms_leave_stone import Message
from urllib.parse import quote
from yunpian_python_sdk.model import constant as yc
from yunpian_python_sdk.ypclient import YunpianClient


class Robot(object):
    def __init__(self, conf, stone, logger, apikey):
        """
        conf 配置实例
        stone 存储实例
        :param conf:
        :param stone:
        """
        self._conf = conf
        self._stone = stone
        self._conn = pymssql.connect(self._conf.get('server', 'ip'), self._conf.get('server', 'user'),
                                     self._conf.get('server', 'password'),
                                     database=self._conf.get('server', 'database'))
        self._cur = self._conn.cursor()
        self._logger = logger
        self._templates = {}
        self._get_templates()
        self._clnt = YunpianClient(apikey)

        pass

    def run(self):
        self._server_query()
        self._save_stone()
        self._send()
        pass

    def _send(self):
        self._logger.debug("开始发送短信")
        result = self._stone.query(Message).filter(Message.status == False).all()
        tel = []
        data_str = []
        for one in result:
            print(self._templates[one.node_name].format(Name=one.EmployeeName))
            data_str.append(self._templates[one.node_name].format(Name=one.EmployeeName))
            print(one.tel)
            tel.append(one.tel)
            one.status = True
        # 短信发送
        if len(tel) and len(data_str):
            param = {yc.MOBILE: ','.join(tel), yc.TEXT: (','.join(self._sms_send(data_str)))}
            self._clnt.sms().multi_send(param)
        self._logger.debug("短信发送完成,共计发送{num}条短信".format(num=len(data_str)))
        self._stone.commit()
        pass

    def _server_query(self):
        """
        调用 _query_stone() 查询本地存储的最后查询的时间，并将其作为起始时间，
        结束时间是当前时间减去半小时
        等待结果被 _save_stone() 调用
        :return:
        """
        self._logger.debug("开始查询超过半小时未处理的离职节点")
        #  min_date_query 语句确定
        query_stone_result = self._query_stone()
        if query_stone_result is None:
            min_date_query = ''
        else:
            min_date_query = "and FCreationDateTime > '{date}'".format(date=query_stone_result)
        # 新流程是从 2017-11-28 10:45:00.000 开始
        sql = """
            select top 100 FID, FCreationDateTime, FActivityDefName ,wbd.EmployeeName, wbd.HRMS_UserField_6 
            from T_WF_RunAssignment as twr
            join Wf_biz_DimissionInfo as wbd on twr.FProcessInstID = wbd.ProcessInsID
            where FProcessDefName like '%百捷员工离职交接%' and FStatus = 0
            and FActivityDefName != '员工关系专员接收'
            and FCreationDateTime > '2017-11-28 10:45:00.000'
            {min_date_query}
            and FCreationDateTime <= DATEADD( minute,-30,GETDATE())
            order by FCreationDateTime desc
        """.format(min_date_query=min_date_query)
        print(sql)
        self._cur.execute(sql)
        self._result = self._cur.fetchall()
        self._logger.debug("查询完成")
        pass

    def _save_stone(self):
        """
        存储查询结果
        :return:
        """
        emp_cols = ('FID', 'FCreationDateTime', 'node_name', 'EmployeeName', 'tel', 'status')
        for one in self._result:
            empinfo = Message()
            for count, col in enumerate(emp_cols):
                if col in ('FID',):
                    setattr(empinfo, col, str(one[count]))
                elif col in ('EmployeeName',):
                    try:
                        int(one[count][len(one[count]) - 1])
                        name = one[count][:len(one[count]) - 1]
                    except ValueError:
                        name = one[count]
                    setattr(empinfo, col, name)
                elif col in ('status',):
                    setattr(empinfo, col, False)
                elif col in ('tel',):
                    # todo 发送给相关负责人，告知手机号码错误
                    # assert len(one[count]) != 11, "手机号码错误"
                    setattr(empinfo, col, one[count])
                else:
                    setattr(empinfo, col, one[count])
            self._stone.add(empinfo)
        self._stone.commit()
        pass

    def _query_stone(self):
        """
        查询最后查询的时间
        :return:
        """
        result = list(self._stone.query(func.max(Message.FCreationDateTime)).one_or_none())[0]
        self._logger.debug("本次查询时间开始值为{date}".format(date=result))
        return result
        pass

    def _get_templates(self):
        for key, value in self._conf.items(section='template'):
            self._templates[key] = value
        pass

    @staticmethod
    def _sms_send(array):
        data_str = []
        for one in array:
            data_str.append(quote(one))
        return data_str
        pass

    pass
