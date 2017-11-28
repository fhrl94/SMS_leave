# 导入:
import sqlite3
import sys

from sqlalchemy import Column, create_engine, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

cx = sqlite3.connect(sys.path[0] + "/emp.sqlite3")
engine = create_engine("sqlite:///" + sys.path[0] + "/emp.sqlite3", echo=True)
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)

# 创建对象的基类:
Base = declarative_base()
# 连接数据库
session = DBSession()


class Message(Base):
    # 表的名字:
    __tablename__ = 'Message'

    # 表的结构:
    id = Column(Integer(), primary_key=True)
    FID = Column(String(36))
    FCreationDateTime = Column(DateTime(36))
    EmployeeName = Column(String(10))
    node_name = Column(String(30))
    tel = Column(String(11))
    status = Column(Boolean())

    def __str__(self):
        return self.id


# 如果没有创建表，则创建
Base.metadata.create_all(engine)


def stoneobject():
    return session
