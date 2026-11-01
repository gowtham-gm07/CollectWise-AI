
import sqlite3
import unittest

from src.schema import DB_PATH


class CollectWiseSystemTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(DB_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_customer_records_exist(self):
        count = self.conn.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        self.assertGreater(count, 0)

    def test_loan_records_exist(self):
        count = self.conn.execute(
            "SELECT COUNT(*) FROM loans"
        ).fetchone()[0]

        self.assertGreater(count, 0)

    def test_installment_relationship(self):
        loans = self.conn.execute(
            "SELECT COUNT(*) FROM loans"
        ).fetchone()[0]

        installments = self.conn.execute(
            "SELECT COUNT(*) FROM installments"
        ).fetchone()[0]

        self.assertEqual(
            installments,
            loans * 3,
            "Each loan must have exactly 3 installments."
        )

    def test_unique_loan_ids(self):
        total, unique = self.conn.execute("""
            SELECT
                COUNT(*),
                COUNT(DISTINCT loan_id)
            FROM loans
        """).fetchone()

        self.assertEqual(total, unique)

    def test_anomaly_labels_exist(self):
        count = self.conn.execute(
            "SELECT COUNT(*) FROM anomaly_labels"
        ).fetchone()[0]

        self.assertEqual(count, 5)

    def test_foreign_key_integrity(self):
        errors = self.conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        self.assertEqual(errors, [])

    def test_installment_amounts_match_loan_principal(self):
        rows = self.conn.execute("""
            SELECT
                l.loan_id,
                l.principal,
                SUM(i.amount_due)
            FROM loans l
            JOIN installments i
                ON l.loan_id = i.loan_id
            GROUP BY l.loan_id, l.principal
        """).fetchall()

        for loan_id, principal, installment_total in rows:
            self.assertAlmostEqual(
                principal,
                installment_total,
                places=2,
                msg=f"Installment total mismatch for {loan_id}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
