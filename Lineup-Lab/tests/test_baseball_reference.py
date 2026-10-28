import pandas as pd

from baseball_lineup_optimizer.data.baseball_reference import import_baseball_reference_hitter_season


def test_import_baseball_reference_hitter_season(monkeypatch):
    class Response:
        text = "<title>Ichiro Suzuki Stats, Height, Weight, Position | Baseball-Reference.com</title>"

    def fake_get(url, timeout):
        return Response()

    def fake_read_html(html):
        return [
            pd.DataFrame(
                [
                    {
                        "Season": "2004*",
                        "Team": "SEA",
                        "PA": 762,
                        "AB": 704,
                        "H": 262,
                        "2B": 24,
                        "3B": 5,
                        "HR": 8,
                        "BB": 49,
                        "HBP": 4,
                        "SO": 63,
                        "SB": 36,
                        "CS": 11,
                    }
                ]
            ),
            pd.DataFrame([{"Season": "2004*", "PA": 762, "Rdp": 6}]),
            pd.DataFrame([{"Season": "2004*", "PA": 762, "LD%": 16.7, "GB%": 62.8, "FB%": 15.3, "XBT%": 64.0}]),
        ]

    monkeypatch.setattr("baseball_lineup_optimizer.data.baseball_reference.requests.get", fake_get)
    monkeypatch.setattr("baseball_lineup_optimizer.data.baseball_reference.pd.read_html", fake_read_html)

    season = import_baseball_reference_hitter_season(
        "https://www.baseball-reference.com/players/s/suzukic01.shtml",
        2004,
    )

    assert season.name == "Ichiro Suzuki 2004"
    assert season.single == 225
    assert season.pa == 762
    assert season.sb == 36
    assert season.rdp == 6.0
    assert season.xbt_rate == 0.64
    assert season.gb_rate == 0.628
