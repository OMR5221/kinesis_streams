# 3. Expression: Add Time Fields
# Add End_Time, Incremenetal_Time, End_Date_Interpolated
# Using some $$START_TIME Parameter possibly set in configuration file?
from datetime import date, datetime, timedelta
from sqlalchemy.ext.declarative import declarative_base

# Define configuration settinngs that can be used to control the queries that call the process:
INTERVAL = 1 # days
MINUTES = 5 # 60 * 24 = # of minutes in a day

minutes_in_timerange = INTERVAL * MINUTES
today = datetime.utcnow().date()
start_dt = datetime.strptime('2018-10-01', '%Y-%m-%d')
# end_dt = datetime(today.year, today.month, today.day)
# start_dt = end_dt - timedelta(days=INTERVAL)

timerange_list = {i: start_dt + timedelta(minutes=i) for i in range(minutes_in_timerange)}

print(start_dt)

print(timerange_list)

# Need to create a table schema:

engine = create_engine('sqlite:///esbi.db')

Base = declarative_base()

class DateRange(Base):
    __tablename__ = 'date_range'

    DateId = Column(Integer, primary_key=True)
    DateStr = Column(String(255))
    DateVal = Column(DateTime)

    '''
    def __init__(self, date_id, date_str, date_val):
        self.DateId = date_id
        self.DateStr = date_str
        self.DateVal = date_val
    '''

    def __repr__(self):
        return "<DateRange('%s')>" % (self.DateStr)

DateRange.__table__.create(bind=engine, checkfirst=True)
