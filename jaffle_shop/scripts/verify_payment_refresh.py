"""Comprueba cambios de estado, pagos nuevos e idempotencia en una BD temporal."""

from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile

import duckdb
import yaml


PROJECT = Path(__file__).resolve().parents[1]


def main():
    # No modifica los CSV ni la base de datos de desarrollo.
    scratch_root = PROJECT / "target"
    scratch_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="jaffle_refresh_", dir=scratch_root) as directory:
        temporary = Path(directory)
        database = temporary / "verification.duckdb"
        profile = {
            "jaffle_shop": {
                "target": "dev",
                "outputs": {"dev": {
                    "type": "duckdb", "path": str(database), "threads": 2,
                }},
            }
        }
        (temporary / "profiles.yml").write_text(yaml.safe_dump(profile), encoding="utf-8")

        def dbt(*arguments):
            command = [
                sys.executable, "-m", "dbt.cli.main", *arguments,
                "--profiles-dir", str(temporary),
                "--target-path", str(temporary / "target"),
                "--log-path", str(temporary / "logs"),
            ]
            result = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace")
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)

        def execute(sql):
            with duckdb.connect(str(database)) as connection:
                connection.execute(sql)

        def verify(expected):
            dbt("run", "--select", "payments_by_method_and_status")
            with duckdb.connect(str(database)) as connection:
                actual = connection.execute(
                    "select payment_method, order_status, total_amount "
                    "from payments_by_method_and_status order by 1, 2"
                ).fetchall()
            if actual != expected:
                raise AssertionError(f"Esperado: {expected}; obtenido: {actual}")

        dbt("seed", "--select", "raw_orders", "raw_payments")
        execute("""
            delete from raw_payments;
            delete from raw_orders;
            insert into raw_orders (id, user_id, order_date, status) values
                (1, 1, '2018-01-01', 'placed'),
                (2, 1, '2018-01-02', 'shipped');
            insert into raw_payments (id, order_id, payment_method, amount) values
                (1, 1, 'credit_card', 1000),
                (2, 1, 'credit_card', 2000),
                (3, 1, 'coupon', 500),
                (4, 2, 'credit_card', 700);
        """)
        verify([
            ("coupon", "placed", Decimal("5.00")),
            ("credit_card", "placed", Decimal("30.00")),
            ("credit_card", "shipped", Decimal("7.00")),
        ])
        print("OK: varios pagos por pedido, metodos separados y conversion a AUD.", flush=True)

        execute("update raw_orders set status = 'shipped' where id = 1")
        verify([
            ("coupon", "shipped", Decimal("5.00")),
            ("credit_card", "shipped", Decimal("37.00")),
        ])
        print("OK: el importe cambia de grupo y desaparecen los grupos vacios.", flush=True)

        execute("insert into raw_payments (id, order_id, payment_method, amount) "
                "values (5, 2, 'credit_card', 1250)")
        expected = [
            ("coupon", "shipped", Decimal("5.00")),
            ("credit_card", "shipped", Decimal("49.50")),
        ]
        verify(expected)
        print("OK: un pago nuevo aumenta el total en 12.50 AUD.", flush=True)
        verify(expected)
        print("OK: repetir la ejecucion no duplica los importes.", flush=True)


if __name__ == "__main__":
    main()
