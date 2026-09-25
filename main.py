import sys
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from notifier import (
    send_headless_notification,
    setup_telegram_wizard,
    send_telegram,
    send_ntfy
)

def main():
    parser = argparse.ArgumentParser(
        description="Headless Productivity Automation & Notification Script",
        epilog="This script runs 100% headlessly in the background with zero browser popups."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: notify
    notify_parser = subparsers.add_parser("notify", help="Send a headless background notification")
    notify_parser.add_argument(
        "-m", "--message",
        type=str,
        default="🚀 Automated Task Alert: Your background script completed successfully!",
        help="Message text to send"
    )

    # Command: setup-telegram
    subparsers.add_parser("setup-telegram", help="30-second setup wizard for Telegram notifications")

    # Command: test
    subparsers.add_parser("test", help="Test your current notification setup")

    args = parser.parse_args()

    if args.command == "notify":
        success = send_headless_notification(args.message)
        sys.exit(0 if success else 1)

    elif args.command == "setup-telegram":
        success = setup_telegram_wizard()
        sys.exit(0 if success else 1)

    elif args.command == "test":
        success = send_headless_notification("🔔 Test Notification: Everything is working headlessly!")
        sys.exit(0 if success else 1)

    else:
        print("=" * 65)
        print("     HEADLESS PRODUCTIVITY AUTOMATION SYSTEM (0 BROWSER)")
        print("=" * 65)
        print("1. Send a headless notification now")
        print("2. Setup Telegram Bot in 30 seconds (Recommended for @ahmedallam111)")
        print("3. Test notification configuration")
        print("4. Exit")
        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "1":
            custom_msg = input("Enter notification message: ").strip()
            msg = custom_msg if custom_msg else "🚀 Automated Task Alert: Script completed successfully!"
            send_headless_notification(msg)
        elif choice == "2":
            setup_telegram_wizard()
        elif choice == "3":
            send_headless_notification("🔔 Test Notification: Everything is working headlessly!")
        else:
            print("Exiting.")

if __name__ == "__main__":
    main()
