from baseball_lineup_optimizer.data.baseball_reference import import_baseball_reference_hitter_season


def test_import_baseball_reference_hitter_season(monkeypatch):
    html = """
    <html>
      <head><title>Ichiro Suzuki Stats, Height, Weight, Position | Baseball-Reference.com</title></head>
      <body>
        <table id="players_standard_batting">
          <tbody>
            <tr>
              <th data-stat="year_id">2004*</th>
              <td data-stat="team_name_abbr">SEA</td>
              <td data-stat="b_pa">762</td>
              <td data-stat="b_ab">704</td>
              <td data-stat="b_h">262</td>
              <td data-stat="b_doubles">24</td>
              <td data-stat="b_triples">5</td>
              <td data-stat="b_hr">8</td>
              <td data-stat="b_bb">49</td>
              <td data-stat="b_hbp">4</td>
              <td data-stat="b_so">63</td>
              <td data-stat="b_sb">36</td>
              <td data-stat="b_cs">11</td>
            </tr>
          </tbody>
        </table>
        <table id="players_value_batting">
          <tbody>
            <tr>
              <th data-stat="year_id">2004*</th>
              <td data-stat="team_name_abbr">SEA</td>
              <td data-stat="b_pa">762</td>
              <td data-stat="b_runs_double_plays">6</td>
            </tr>
          </tbody>
        </table>
        <table id="players_advanced_batting">
          <tbody>
            <tr>
              <th data-stat="year_id">2004*</th>
              <td data-stat="team_name_abbr">SEA</td>
              <td data-stat="b_pa">762</td>
              <td data-stat="b_ld_perc">16.7%</td>
              <td data-stat="b_gb_perc">62.8%</td>
              <td data-stat="b_fb_perc">15.3%</td>
              <td data-stat="b_extra_bases_taken_perc">64.0%</td>
            </tr>
          </tbody>
        </table>
      </body>
    </html>
    """

    class Response:
        text = html

        @staticmethod
        def raise_for_status():
            return None

    def fake_get(url, timeout, headers):
        assert "LineupOptimizer" in headers["User-Agent"]
        return Response()

    monkeypatch.setattr("baseball_lineup_optimizer.data.baseball_reference.requests.get", fake_get)

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