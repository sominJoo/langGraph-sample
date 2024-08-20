import sqlite3

import pandas as pd


class DBSetting:
    def connect_db(self, db):
        # DB 연결
        conn = sqlite3.connect(db)

        self.set_pandas_data(conn)
        conn.commit()
        conn.close()

    @staticmethod
    def set_pandas_data(conn):
        """ Pandas 데이터 설정 """
        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table';", conn
        ).name.tolist()
        tdf = {}
        for t in tables:
            tdf[t] = pd.read_sql(f"SELECT * from {t}", conn)

        example_time = pd.to_datetime(
            tdf["flights"]["actual_departure"].replace("\\N", pd.NaT)
        ).max()
        current_time = pd.to_datetime("now").tz_localize(example_time.tz)
        time_diff = current_time - example_time

        tdf["bookings"]["book_date"] = (
                pd.to_datetime(tdf["bookings"]["book_date"].replace("\\N", pd.NaT), utc=True)
                + time_diff
        )

        datetime_columns = [
            "scheduled_departure",
            "scheduled_arrival",
            "actual_departure",
            "actual_arrival",
        ]
        for column in datetime_columns:
            tdf["flights"][column] = (
                    pd.to_datetime(tdf["flights"][column].replace("\\N", pd.NaT)) + time_diff
            )

        for table_name, df in tdf.items():
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        del df
        del tdf
