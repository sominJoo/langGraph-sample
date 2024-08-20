import sqlite3
from datetime import datetime, date
from typing import Optional, Union

from langchain.tools import tool


@tool
def search_hotels(
        location: Optional[str] = None,
        name: Optional[str] = None,
) -> list[dict]:
    """
    위치, 이름, 가격 계층, 체크인 날짜, 체크아웃 날짜를 기준으로 호텔을 검색합니다
    :param location:
    :param name:
    :return: 검색 기준과 일치하는 호텔 목록
    """
    local_db_file = "travel2.sqlite"
    conn = sqlite3.connect(local_db_file)
    cursor = conn.cursor()

    query = "SELECT * FROM hotels WHERE 1=1"
    params = []

    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    # For the sake of this tutorial, we will let you match on any dates and price tier.
    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()

    return [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]


@tool
def book_hotel(hotel_id: int) -> str:
    """
    Book a hotel by its ID.

    Args:
        hotel_id (int): The ID of the hotel to book.

    Returns:
        str: A message indicating whether the hotel was successfully booked or not.
    """
    local_db_file = "travel2.sqlite"
    conn = sqlite3.connect(local_db_file)
    cursor = conn.cursor()

    cursor.execute("UPDATE hotels SET booked = 1 WHERE id = ?", (hotel_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully booked."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."


@tool
def update_hotel(
        hotel_id: int,
        checkin_date: Optional[Union[datetime, date]] = None,
        checkout_date: Optional[Union[datetime, date]] = None,
) -> str:
    """
    호텔 예약 내역 수정
    :param hotel_id:
    :param checkin_date:
    :param checkout_date:
    :return:
    """
    local_db_file = "travel2.sqlite"
    conn = sqlite3.connect(local_db_file)
    cursor = conn.cursor()

    if checkin_date:
        cursor.execute(
            "UPDATE hotels SET checkin_date = ? WHERE id = ?", (checkin_date, hotel_id)
        )
    if checkout_date:
        cursor.execute(
            "UPDATE hotels SET checkout_date = ? WHERE id = ?",
            (checkout_date, hotel_id),
        )

    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully updated."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."


@tool
def cancel_hotel(hotel_id: int) -> str:
    """
    호텔 취소
    :param hotel_id:
    :return:
    """
    local_db_file = "travel2.sqlite"
    conn = sqlite3.connect(local_db_file)
    cursor = conn.cursor()

    cursor.execute("UPDATE hotels SET booked = 0 WHERE id = ?", (hotel_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Hotel {hotel_id} successfully cancelled."
    else:
        conn.close()
        return f"No hotel found with ID {hotel_id}."
