#!/usr/bin/env python3
"""
Quick start entry – launches interactive CLI
"""
from cli import app
import sys

if __name__ == "__main__":
    # If no args, launch interactive mode
    if len(sys.argv) == 1:
        # Launch interactive directly
        from cli import interactive as inter_cmd
        import typer
        # Call interactive command
        try:
            from bot.config import Config
            errors = Config.validate()
            if errors and not Config.MOCK_TRADING:
                print("⚠️  API Configuration Missing")
                for e in errors:
                    print(f" • {e}")
                print("\nSetup:\n 1. cp .env.example .env\n 2. Add your Testnet keys from https://testnet.binancefuture.com")
                print("\nOr set MOCK_TRADING=true in .env to run in offline demo mode.")
                sys.exit(1)
            elif errors and Config.MOCK_TRADING:
                print("ℹ️  API credentials missing – running in MOCK_TRADING mode (offline demo)")
            # Run interactive
            inter_cmd()
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        app()
