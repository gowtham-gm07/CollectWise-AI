
import argparse

from src.data_generator import generate_base_data
from src.payment_engine import run_payment_engine
from src.delinquency_engine import run_delinquency_engine
from src.promise_engine import run_promise_engine
from src.contact_engine import run_contact_engine
from src.anomaly_engine import run_anomaly_engine
from src.validator import run_validation
from src.exporter import export_data


def main():
    parser = argparse.ArgumentParser(
        description="CollectWise AI - Collections Data Engine"
    )

    parser.add_argument(
        "--loans",
        type=int,
        default=500,
        help="Number of loans to generate"
    )

    args = parser.parse_args()

    if args.loans < 1:
        parser.error("--loans must be at least 1")

    print("\n====================================")
    print("       COLLECTWISE AI ENGINE")
    print("====================================")

    print("\n[1/7] Generating baseline data...")
    generate_base_data(args.loans)

    print("\n[2/7] Processing payments...")
    run_payment_engine()

    print("\n[3/7] Calculating delinquency...")
    run_delinquency_engine()

    print("\n[4/7] Tracking promises...")
    run_promise_engine()

    print("\n[5/7] Generating contact attempts...")
    run_contact_engine()

    print("\n[6/7] Injecting labelled anomalies...")
    run_anomaly_engine()

    print("\n[7/7] Validating and exporting...")
    run_validation()
    export_data()

    print("\n====================================")
    print("COLLECTWISE AI PIPELINE COMPLETED")
    print("====================================")


if __name__ == "__main__":
    main()
