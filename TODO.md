# Список задач для демо-приложения

- [ ] Аутентификация для пользователя через AzureAD
  - У нас secure-клиент т.к. нет SPA, а фронт генерируется на беке
  - Нужно понять как MSAL скрестить с FastAPI

- [ ] Сделать ключ для запуска: ***--worker***, если он установлен то приложение запускается как обработчик запросов (worker)
  - При таком запуске фронтенд должен быть другим - только показывать статус и параметры запроса, без возможности входа

- [ ] Сделать сервис для обработки событий из Service Bus, посмотреть библиотеки MS под это
  - Сервис должен в фоне выгребать сообщения, делать запись в CosmosDB о них

- [ ] Аунтетификация в Service Bus и CosmosDB должна быть через Managed Identity
  - Как managed identity работает с Container App. Это System or User identity? Вероятно User что бы права не выставлять при каждом удалении приложения

- [ ] Сервис для сохранения в БД (repository). Работает через нативную библиотеку MS, вызывается из сервиса обработки входящих сообщений из очереди.
  - Нужен ли Singleton или можно создавать объект на каждый запрос

- [ ] Интеграция с AppInsght - логи, метрики, запросы

- [ ] Использование App Configuration для хранения параметров

- [ ] Автоматическая сборка образа (одного) и деплой двух приложений в кластер
  - Вынести deploy как отдельный template? Или сделать кастомный пайплайн не являющийся extend'ом

- [ ] Сделать terraform для деплоя инфраструктуры для приложения
  - Container App Environment
  - Azure Service Bus
  - App Configuration
  - ConsmosDB
  - Managed Identity

# Аутентификация через MSAL

## 1. FastAPI/MSAL
**Homepage**: [https://github.com/dudil/fastapi_msal/tree/master](https://github.com/dudil/fastapi_msal/tree/master)

#### Возможности

- Поддерживает реализацию **OAuth Authorization Code Flow** с помощью MSAL
- Предоставляет API-endpoint'ы для login/token (back-channel)/logout и свой роутер.
- Поддерживает хранение токена в in-memory кеше, привязанном к сессии пользователя (внутри cookie сессии хранится только ID)
- Поддерживает проверку Bearer-токена в заголовке Authentication (если токен получен как-то еще, например в Swagger)
  - Кажется поддерживает только передачу ID-токена в заголовке, и не поддерживает Access-токен
- Есть функции для получения behalf-of токена для вызова других API

#### Использование

1. Требуется добавить ***SessionMiddleware*** для поддержки сессий и cookies (данные сессии хранятся в них)
2. Создать объект ***MSALClientConfig*** с конфигурацией
3. Создать глобальный экземпляр ***MSALAuthorization***, который внутри создает объект *ConfidentialClientApplication*. Cхема включения:
   - *MSALAuthorization* (глобальный объект)
     - *MSALAuthCodeHandler* (глобальный объект, создается в *MSALAuthorization.init()*)
       - *AsyncConfClient* (создается по запросу в *MSALAuthCodeHandler.msal_app()*)
         - *ConfidentialClientApplication* (создается по запросу, в *AsyncConfClient.init()*)
4. Добавить роутер (он добавляет пути /login, /logout, /token для Code Authorization)

   ```python
   app.include_router(msal_auth.router)
   ```

5. Добавить зависимость *Depends(msal_auth.scheme)*

    ```Python
    @app.get("/users/me", response_model=UserInfo, response_model_exclude_none=True, response_model_by_alias=False)
    async def read_users_me(current_user: UserInfo = Depends(msal_auth.scheme)) -> UserInfo:
        return current_user
    ```

#### Официальный пример

```python
import uvicorn
from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware
from fastapi_msal import MSALAuthorization, UserInfo, MSALClientConfig

client_config: MSALClientConfig = MSALClientConfig()
client_config.client_id = "The client_id retrieved at step #1"
client_config.client_credential = "The client_credential retrieved at step #1"
client_config.tenant = "Your tenant_id retrieved at step #1"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="SOME_SSH_KEY_ONLY_YOU_KNOW")  # replace with your own!!!
msal_auth = MSALAuthorization(client_config=client_config)
app.include_router(msal_auth.router)


@app.get("/users/me", response_model=UserInfo, response_model_exclude_none=True, response_model_by_alias=False)
async def read_users_me(current_user: UserInfo = Depends(msal_auth.scheme)) -> UserInfo:
    return current_user


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=5000, reload=True)

```
## fastapi-aad-auth

**Homepage:** [https://djpugh.github.io/fastapi_aad_auth/index.html](https://djpugh.github.io/fastapi_aad_auth/index.html)
**Repo:** [https://github.com/djpugh/fastapi_aad_auth/tree/main](https://github.com/djpugh/fastapi_aad_auth/tree/main)

#### Возможности

- Поддержка  **OAuth Authorization Code Flow**
- UI для логина
- Валидация токенов в запросах
- Middleware для установки данных user'а в Request'ах
- Декораторы для path-функций

#### Использование

Общее ощущение от документации и кода: СЛОЖНО
Разбираться долго и сложно

Но кажется это самый комплексный проект. Но не развивавшийся (кроме обновления зависимостей) с 2022 года.


## FastAPI-Azure-Auth

**Homepage:** [https://intility.github.io/fastapi-azure-auth/](https://intility.github.io/fastapi-azure-auth/)
**Repo:** [https://github.com/Intility/FastAPI-Azure-Auth](https://github.com/Intility/FastAPI-Azure-Auth)

#### Возможности

- Поддержка аутентификации API-запросов через токены AzureAD для Azure AD и Azure AD B2C (single & multi-tenant apps)
- Автоматическое получение OpenIDConnect конфигурации из провайдера
- Реализует стандартное для FastAPI auth scheme, которую можно передать как зависимость в Security()
- Нет своей реализации получения токена "on behalf of" - в демо-примере вызывается endpoint AzureAD через *httpx*
- Фактически это только средство валидации bearer-токена, но учитывающее claim'ы и особенности AzureAD

#### Использование

- Создать экземпляр класса ***SingleTenantAzureAuthorizationCodeBearer***
- Вызвать загрузку конфигурации OpenID Connect при старте приложения (`azure_scheme.openid_config.load_config()`)
- Передать созданный экземпляр как зависимость Security() в path-функции

#### Официальный пример

```Python
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

# ==== Skip  =====================

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes=settings.SCOPES,
)

@app.on_event('startup')
async def load_config() -> None:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()

@app.get("/", dependencies=[Security(azure_scheme)])
async def root():
    return {"message": "Hello World"}


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
```

