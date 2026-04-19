# 🚀 Deploying NEXUS to Render

Follow these steps to deploy your Smart Load Balancer Simulator to the cloud.

## 1. Push Changes to GitHub
First, make sure all the latest changes (including the updated `Dockerfile` and `render.yaml`) are pushed to your GitHub repository:
```powershell
git add .
git commit -m "chore: prepare for render deployment"
git push origin main
```

## 2. Connect to Render
1. Go to [dashboard.render.com](https://dashboard.render.com) and log in.
2. Click **Blueprints** in the top navigation bar.
3. Click **New Blueprint Instance**.
4. Connect your GitHub account and select the **`smart_load_balancer`** repository.

## 3. Configure the Deployment
Render will detect the `render.yaml` file and automatically configure the service.
- **Service Name**: `nexus-load-balancer`
- **Environment**: `Docker`

### Environment Variables
You will be prompted to fill in some variables. Most are pre-set, but for the **Feedback System** (Email) to work, you should provide:
- `SMTP_HOST`: e.g., `smtp.gmail.com`
- `SMTP_USER`: Your Gmail address.
- `SMTP_PASSWORD`: Your 16-character [App Password](https://myaccount.google.com/apppasswords).

> [!TIP]
> You can leave these blank for now if you just want to see the dashboard. You can add them later in the **Environment** tab of your Render service.

## 4. Deploy!
Click **Apply**. Render will now:
1. Build your Docker image.
2. Deploy it to a global URL (e.g., `nexus-load-balancer.onrender.com`).
3. Handle the port mapping automatically.

## 5. Verify the Live Dash
Once the deployment is "Live":
1. Open your new Render URL.
2. Check the **WebSocket Status** in the top right. It should say `CONNECTED`.
3. Try starting the simulation and watch the real-time traffic flow!

---
**Need help?** If the build fails, check the "Events" or "Logs" tab in Render for error details.
