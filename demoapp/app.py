import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi_msal import MSALAuthorization, UserInfo, MSALClientConfig
from demoapp.security import MSALOptionalScheme, get_auth_config

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("AUTH_SESSION_KEY","demokey"))

auth_config = get_auth_config()
msal_auth = MSALAuthorization(client_config=auth_config)
app.include_router(msal_auth.router)

tpl_path = Path(__file__).absolute().parent.joinpath("templates")
templates = Jinja2Templates(directory=tpl_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

root_auth_scheme = MSALOptionalScheme(scheme=msal_auth.scheme, auth_required=False)

# Path functions (API controllers)
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request, current_user: UserInfo = Depends(root_auth_scheme)):
    if current_user:
        username = current_user.preferred_username
    else:
        username = None

    return templates.TemplateResponse("main.html.j2", {
        "request": request,
        "username": username,
        "login_path": auth_config.login_path,
        "logout_path": auth_config.logout_path
    })
