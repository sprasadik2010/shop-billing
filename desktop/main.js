const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let backendProcess;

function startBackend() {
  const backendExe = path.join(
    process.resourcesPath || __dirname,
    "backend",
    "main.exe"
  );

  backendProcess = spawn(backendExe, [], {
    cwd: path.dirname(backendExe),
  });

  backendProcess.stdout.on("data", (data) =>
    console.log("FastAPI:", data.toString())
  );

  backendProcess.stderr.on("data", (data) =>
    console.error("FastAPI Error:", data.toString())
  );
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (!app.isPackaged) {
    // Dev mode → Vite
    win.loadURL("http://localhost:5173");
  } else {
    // Production → load from app.asar/dist/
    const indexPath = path.join(
      __dirname,
      "frontend-ts",
      "dist",
      "index.html"
    );
    win.loadFile(indexPath);
  }
}

app.whenReady().then(() => {
  startBackend();

  // Give backend time to start
  setTimeout(() => {
    createWindow();
  }, 1500);
});

app.on("window-all-closed", () => {
  if (backendProcess) backendProcess.kill();
  app.quit();
});
