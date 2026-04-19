# 📧 Gmail SMTP Setup Guide

To enable real-time feedback delivery to your Gmail, follow these steps to bypass standard password blocks.

## 1. Create a `.env` File
In your project root, create a file simply named `.env`. Copy the contents from `.env.example` into it.

## 2. Generate a Gmail App Password
Standard passwords will **not** work for SMTP security reasons.
1. Go to your [Google Account Settings](https://myaccount.google.com/).
2. Select **Security** on the left menu.
3. Under "How you sign in to Google," select **2-Step Verification** (it must be ON).
4. Scroll to the bottom and select **App passwords**.
5. Enter a name (e.g., "Nexus Simulator") and click **Create**.
6. Copy the **16-character code** provided.

## 3. Populate `.env`
Update your `.env` file with the following:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=arorapratham758@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # The 16-character code you just copied
SMTP_TLS=True
```


## 4. Test
1. Restart the simulator: `python run.py`.
2. Go to **Settings** > **Direct Feedback**.
3. Send a test message.
4. Check your Gmail inbox!

> [!IMPORTANT]
> Keep your App Password secret. It allows full access to your email for this specific application.
