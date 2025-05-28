#!/usr/bin/env python3
"""
Test script for Resend email integration.
"""

import json
from email_notifications import ResendEmailNotifier
from utils import logger

def test_email_integration():
    """Test the Resend email integration."""
    print("Testing Resend email integration...")
    
    # Load config
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    
    # Initialize email notifier
    email_notifier = ResendEmailNotifier(config.get("notifications", {}))
    
    # Test connection
    if not email_notifier.test_email_connection():
        print("❌ Email connection test failed")
        return False
    
    print("✅ Email connection test passed")
    
    # Create mock analysis results for testing
    mock_results = [
        {
            "name": "Test Site 1",
            "url": "https://example.com/test1",
            "status": "analyzed",
            "analysis": {
                "rating": "4",
                "analysis": "Detta är en testanalys med högt betyg.",
                "extracted_news": [
                    {
                        "title": "Viktig testnyhet",
                        "date": "2025-05-27",
                        "rating": 4,
                        "snippet": "Detta är en viktig testnyhet som borde skickas via email."
                    },
                    {
                        "title": "Mindre viktig nyhet",
                        "date": "2025-05-27", 
                        "rating": 2,
                        "snippet": "Detta är en mindre viktig nyhet."
                    }
                ]
            }
        },
        {
            "name": "Test Site 2",
            "url": "https://example.com/test2",
            "status": "analyzed",
            "analysis": {
                "rating": "2",
                "analysis": "Detta är en testanalys med lågt betyg.",
                "extracted_news": [
                    {
                        "title": "Rutinuppdatering",
                        "date": "2025-05-27",
                        "rating": 2,
                        "snippet": "Detta är en rutinuppdatering."
                    }
                ]
            }
        }
    ]
    
    # Test if notification should be sent
    should_send = email_notifier.should_send_notification(mock_results)
    print(f"Should send notification: {should_send}")
    
    # Test email content formatting
    if should_send:
        email_content = email_notifier.format_email_content(mock_results)
        print(f"Email subject: {email_content['subject']}")
        print("Email content formatted successfully")
        
        # Optionally send test email (uncomment to actually send)
        # print("Sending test email...")
        # success = email_notifier.send_summary_email(mock_results)
        # if success:
        #     print("✅ Test email sent successfully!")
        # else:
        #     print("❌ Failed to send test email")
    
    return True

if __name__ == "__main__":
    success = test_email_integration()
    
    if success:
        print("\n✅ Email integration test completed successfully!")
    else:
        print("\n❌ Email integration test failed!") 