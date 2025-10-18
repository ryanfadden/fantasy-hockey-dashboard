"""
ESPN Cookie Extractor Helper
Helps users extract ESPN authentication cookies
"""

import webbrowser
import time


def print_cookie_extraction_guide():
    """Print detailed guide for extracting ESPN cookies"""
    print("🍪 ESPN Cookie Extraction Guide")
    print("=" * 60)
    print()
    print("Follow these steps to get your ESPN authentication cookies:")
    print()
    print("1. 🌐 Open your web browser")
    print("2. 🔗 Go to: https://fantasy.espn.com/hockey/")
    print("3. 🔑 Log into your ESPN account")
    print("4. 🏒 Navigate to your fantasy hockey league")
    print("5. 🔧 Open Developer Tools:")
    print("   - Chrome/Edge: Press F12 or Ctrl+Shift+I")
    print("   - Firefox: Press F12 or Ctrl+Shift+I")
    print("   - Safari: Press Cmd+Option+I")
    print()
    print("6. 📋 In Developer Tools:")
    print("   - Click on 'Application' tab (Chrome/Edge)")
    print("   - Click on 'Storage' tab (Firefox)")
    print("   - Click on 'Cookies' in the left sidebar")
    print("   - Select 'https://fantasy.espn.com'")
    print()
    print("7. 🔍 Find these cookies:")
    print("   - Look for 'espn_s2' (long string)")
    print("   - Look for 'SWID' (UUID format)")
    print()
    print("8. 📝 Copy the values:")
    print("   - Right-click on the cookie value")
    print("   - Select 'Copy'")
    print()
    print("9. ⚠️  Important:")
    print("   - Keep these cookies secure")
    print("   - Don't share them with others")
    print("   - They expire periodically, so you may need to refresh them")
    print()
    print("10. 🔄 If cookies don't work:")
    print("    - Try logging out and back in")
    print("    - Clear browser cookies and log in again")
    print("    - Make sure you're in the correct league")
    print()


def open_espn_fantasy():
    """Open ESPN Fantasy Hockey in browser"""
    print("🌐 Opening ESPN Fantasy Hockey...")
    webbrowser.open("https://fantasy.espn.com/hockey/")
    print("✅ Browser opened. Follow the cookie extraction guide above.")


def validate_cookie_format(espn_s2: str, swid: str) -> bool:
    """Validate cookie format"""
    print("🔍 Validating cookie format...")

    # Check espn_s2 format (should be a long string)
    if not espn_s2 or len(espn_s2) < 50:
        print("❌ ESPN_S2 appears to be invalid (too short)")
        return False

    # Check SWID format (should be UUID-like)
    if not swid or len(swid) != 36 or swid.count("-") != 4:
        print("❌ SWID appears to be invalid (should be UUID format)")
        return False

    print("✅ Cookie format looks valid")
    return True


def main():
    """Main function"""
    print_cookie_extraction_guide()

    # Ask if user wants to open ESPN
    open_browser = input(
        "Would you like me to open ESPN Fantasy Hockey for you? (y/N): "
    ).lower()
    if open_browser == "y":
        open_espn_fantasy()

    print("\n" + "=" * 60)
    print("Once you have your cookies, run 'python setup.py' to configure the system.")
    print("=" * 60)


if __name__ == "__main__":
    main()


