import sqlite3
from datetime import date, datetime
from typing import Optional, Union
from langchain.tools import tool


class CarRentalTools:
    def __init__(self, db_path: str):
        self.db = db_path

    @tool
    def search_car_rentals(
            self,
            location: Optional[str] = None,
            name: Optional[str] = None,
    ) -> list[dict]:
        """
        위치, 이름, 가격, 시작, 종료일 기준으로 렌터카 검색
        :param location:
        :param name:
        :return:검색 기준과 일치하는 렌터카 목록입니다.
        """
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        query = "SELECT * FROM car_rentals WHERE 1=1"
        params = []

        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        # For our tutorial, we will let you match on any dates and price tier.
        # (since our toy dataset doesn't have much data)
        cursor.execute(query, params)
        results = cursor.fetchall()

        conn.close()

        return [
            dict(zip([column[0] for column in cursor.description], row)) for row in results
        ]

    @tool
    def book_car_rental(self, rental_id: int) -> str:
        """
        아이디로 렌트카를 예약합니다.
        :param rental_id:
        :return: 성공적으로 예약되었는지 여부
        """
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute("UPDATE car_rentals SET booked = 1 WHERE id = ?", (rental_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Car rental {rental_id} successfully booked."
        else:
            conn.close()
            return f"No car rental found with ID {rental_id}."

    @tool
    def update_car_rental(self,
                          rental_id: int,
                          start_date: Optional[Union[datetime, date]] = None,
                          end_date: Optional[Union[datetime, date]] = None,
                          ) -> str:
        """
    렌터카 시작일과 종료일을 ID로 업데이트합니다.

        :param rental_id:
        :param start_date:
        :param end_date:
        :return:성공적으로 업데이트되었는지 여부
        """
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        if start_date:
            cursor.execute(
                "UPDATE car_rentals SET start_date = ? WHERE id = ?",
                (start_date, rental_id),
            )
        if end_date:
            cursor.execute(
                "UPDATE car_rentals SET end_date = ? WHERE id = ?", (end_date, rental_id)
            )

        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Car rental {rental_id} successfully updated."
        else:
            conn.close()
            return f"No car rental found with ID {rental_id}."

    @tool
    def cancel_car_rental(self, rental_id: int) -> str:
        """
        ID로 차량 대여를 취소합니다.
        :param rental_id:
        :return:
        """
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()

        cursor.execute("UPDATE car_rentals SET booked = 0 WHERE id = ?", (rental_id,))
        conn.commit()

        if cursor.rowcount > 0:
            conn.close()
            return f"Car rental {rental_id} successfully cancelled."
        else:
            conn.close()
            return f"No car rental found with ID {rental_id}."
