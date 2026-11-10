import numpy as np
import pandas as pd
import pytest

from src import config_columns as cfg
from src.data import generate


def test_esquema_y_filas():
    df, arq = generate.generar(300, semilla=1)
    assert list(df.columns) == cfg.EXPECTED_COLUMNS
    assert len(df) == 300 and df.customer_id.is_unique
    assert (arq == "ruido").all()


def test_misma_semilla_mismo_dataset_y_semilla_distinta_cambia():
    a, _ = generate.generar(200, semilla=5, estructura=0.5)
    b, _ = generate.generar(200, semilla=5, estructura=0.5)
    c, _ = generate.generar(200, semilla=6, estructura=0.5)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_derivadas_son_coherentes_con_las_base():
    df, _ = generate.generar(500, semilla=2)
    assert np.allclose(df.total_spent_usd, df.total_purchases * df.avg_order_value_usd, atol=0.01)
    assert (df.rfm_score == df.recency_score + df.frequency_score + df.monetary_score).all()
    assert (df.customer_profitability_usd.round(2) == (df.customer_lifetime_value_usd - df.customer_acquisition_cost_usd).round(2)).all()


def test_sin_estructura_variables_independientes():
    df, _ = generate.generar(5000, semilla=3, estructura=0)
    c = df[["total_purchases", "days_since_last_purchase", "satisfaction_score", "complaint_count"]].corr().abs().to_numpy()
    assert np.max(c[np.triu_indices(4, k=1)]) < 0.06


def test_se_conserva_la_relacion_frecuencia_recencia_del_original():
    from src.data import diagnostico
    df, _ = generate.generar(6000, semilla=8, estructura=0)
    assert diagnostico.razon_correlacion(df.purchase_frequency, df.days_since_last_purchase) > 0.9
    con, _ = generate.generar(6000, semilla=8, estructura=1.0)
    assert (generate.frecuencia_desde_dias(con.days_since_last_purchase) == con.purchase_frequency).mean() > 0.99


def test_con_estructura_aparecen_grupos_y_el_csv_no_trae_la_etiqueta():
    df, arq = generate.generar(3000, semilla=3, estructura=1.0)
    assert "arquetipo" not in df.columns
    assert set(arq) == set(generate.ARQUETIPOS)
    medias = df.groupby(arq.to_numpy()).days_since_last_purchase.mean()
    assert medias["en_riesgo"] > 3 * medias["leal_frecuente"]


def test_validaciones_de_la_linea_de_comandos(tmp_path):
    with pytest.raises(SystemExit):
        generate.main(["--rows", "0"])
    with pytest.raises(SystemExit):
        generate.main(["--rows", "10", "--estructura", "2"])
    salida = tmp_path / "x.csv"
    generate.main(["--rows", "50", "--seed", "9", "--output", str(salida)])
    assert len(pd.read_csv(salida)) == 50
