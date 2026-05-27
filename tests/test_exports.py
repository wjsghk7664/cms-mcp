from __future__ import annotations

from cms_mcp.tools.exports import _rows_to_csv, _sales_rows, _unit_rows


def test_rows_to_csv_uses_union_of_fields() -> None:
    csv_text = _rows_to_csv(
        [
            {"date": "2026-05-26", "total": 10},
            {"date": "2026-05-27", "AOS_HOME": 3},
        ]
    )

    assert csv_text.splitlines()[0] == "date,total,AOS_HOME"
    assert "2026-05-27,,3" in csv_text


def test_sales_rows_flattens_platform_positions() -> None:
    rows = _sales_rows(
        {
            "dataByPlatform": {
                "ANDROID": [
                    {
                        "date": "2026-05-26",
                        "total": 10,
                        "status": "Estimated",
                        "positions": [{"label": "HOME", "total": 3}],
                    }
                ],
                "IOS": [
                    {
                        "date": "2026-05-26",
                        "total": 7,
                        "positions": [{"label": "HOME", "total": 2}],
                    }
                ],
            }
        }
    )

    assert rows == [
        {
            "date": "2026-05-26",
            "total": 17.0,
            "status": "Estimated",
            "AOS_HOME": 3.0,
            "IOS_HOME": 2.0,
        }
    ]


def test_unit_rows_flattens_nested_unit_and_inventory() -> None:
    rows = _unit_rows(
        [
            {
                "unit": {
                    "unitId": 3274,
                    "supplier": "ADSENSE",
                    "label": "banner",
                    "isReporting": True,
                },
                "inventory": {
                    "inventoryId": 222,
                    "project": {"code": "TROST", "name": "트로스트"},
                    "publisher": {"code": "CASHWALK", "nameKr": "캐시워크"},
                    "screenName": "홈",
                    "locationName": "중앙",
                },
            }
        ]
    )

    assert rows[0]["unit_id"] == 3274
    assert rows[0]["project_code"] == "TROST"
    assert rows[0]["supplier"] == "ADSENSE"
