# Skill — Django REST Framework patterns

DRF conventions for Django {{framework_version}} services. Auto-loaded
when adding API endpoints, serializers, or DRF config.

## When to use what

| Endpoint shape                           | Pick                                |
|------------------------------------------|-------------------------------------|
| Standard CRUD on a model                 | `ModelViewSet`                      |
| Read-only collection / detail            | `ReadOnlyModelViewSet`              |
| Custom non-CRUD endpoint                 | `APIView` or `@api_view` decorator  |
| Mixed (e.g. list + custom action)        | `ModelViewSet` + `@action`          |

## Serializers

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ["id", "email", "display_name", "created_at"]
        read_only_fields = ["id", "created_at"]
```

- **Explicit `fields = [...]`** — never `fields = "__all__"`.
  "__all__" leaks new fields automatically + makes API contracts
  unstable.
- **Two serializers when input ≠ output.** A common case :
  `UserCreateSerializer` (accepts `password`) + `UserSerializer`
  (returns `id`, `email`, never `password`).
- **`source=` for renames** : `display_name = serializers.CharField(source="displayName")`
  when the API uses camelCase + the model snake_case.
- **`SerializerMethodField` for computed fields** :
  ```python
  full_name = serializers.SerializerMethodField()
  def get_full_name(self, obj: User) -> str:
      return f"{obj.first_name} {obj.last_name}"
  ```

## ViewSets

```python
class UserViewSet(viewsets.ModelViewSet):
    queryset           = User.objects.select_related("profile").all()
    serializer_class   = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, OrderingFilter]
    filterset_fields   = ["is_active", "role"]
    ordering_fields    = ["created_at", "email"]
    ordering           = ["-created_at"]                 # default

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.activate()
        return Response(self.get_serializer(user).data)
```

- **`queryset` with `select_related` / `prefetch_related`** at the
  class level — N+1 prevention by default.
- **`get_serializer_class`** to switch between create / detail
  serializers per action.
- **`@action(detail=True/False)`** for custom endpoints beyond the
  CRUD shape : `POST /users/{id}/activate/`.

## Router wiring

```python
# src/apps/users/urls.py
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet)

urlpatterns = router.urls
```

- **`DefaultRouter`** generates the standard URL patterns
  (`/users/`, `/users/{pk}/`, `/users/{pk}/activate/`).
- **Mount under `/api/v1/`** in the root urls.py to version cleanly.

## Permissions

| Class                          | Effect                                                |
|--------------------------------|-------------------------------------------------------|
| `AllowAny`                     | No auth check (default for public endpoints).         |
| `IsAuthenticated`              | Must be logged in.                                    |
| `IsAdminUser`                  | `user.is_staff = True`.                               |
| `DjangoModelPermissions`       | Bound to `auth.add_user` / `auth.change_user` perms.  |
| `IsAuthenticatedOrReadOnly`    | SAFE methods open ; mutations require auth.           |

Custom permission :

```python
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj) -> bool:
        return obj.owner_id == request.user.id

permission_classes = [IsAuthenticated, IsOwner]
```

- **`has_permission`** is checked on the view level (before fetching
  the object).
- **`has_object_permission`** is checked after `.get_object()`.
- **Stack permissions** : all must pass. For OR logic, use
  `IsAdminUser | IsOwner` (DRF supports operator overloading).

## Pagination

```python
# src/apps/api/pagination.py
class StandardPagination(PageNumberPagination):
    page_size            = 20
    page_size_query_param = "page_size"
    max_page_size        = 100
```

```toml
# settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.api.pagination.StandardPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.UserRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"user": "1000/hour", "anon": "100/hour"},
}
```

- **One pagination style for the whole API.** Page-number is the
  default ; switch to cursor (`CursorPagination`) only for large /
  unbounded collections.
- **Throttling at the framework level** — every endpoint is
  throttled, override with `throttle_classes = []` for public
  unmetered endpoints (rare).

## Authentication

- **JWT via `djangorestframework-simplejwt`.** Built-in
  `/api/token/` + `/api/token/refresh/` views.
- **Session auth only for the admin** (already wired).
- **API key auth via a custom class** if you have machine-to-machine
  callers — never mix API keys with user JWTs in the same view.

## OpenAPI / Swagger

Use `drf-spectacular` to auto-generate :

```toml
INSTALLED_APPS = [..., "drf_spectacular"]
REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"

SPECTACULAR_SETTINGS = {
    "TITLE":       "{{root_package}} API",
    "DESCRIPTION": "<one-line>",
    "VERSION":     "0.1.0",
}
```

Then in URLs :

```python
path("schema/",     SpectacularAPIView.as_view(),    name="schema"),
path("schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
```

- **Decorate views with `@extend_schema(...)`** when the auto-detected
  shape isn't right (custom responses, deprecation, examples).
- **Generate the spec on CI** (`./manage.py spectacular --file schema.yml`)
  and check it in if downstream clients are generated from it.

## Error responses

DRF renders validation errors as :

```json
{"email": ["Enter a valid email address."], "password": ["This field is required."]}
```

For consistency with the rest of the org, add a uniform shape via a
custom exception handler in `REST_FRAMEWORK["EXCEPTION_HANDLER"]`.

## Anti-patterns

- **No `fields = "__all__"`.** Always explicit.
- **No `permission_classes = [AllowAny]`** unless the endpoint is
  truly public (login, register, healthcheck). Default to
  `IsAuthenticated`.
- **No N+1 in viewsets.** `queryset` carries the right prefetches.
- **No business logic in serializers' `create()` / `update()`.**
  Delegate to `services.py`. Serializers validate + serialise — the
  domain operation belongs in a service.
- **Don't ship `BrowsableAPIRenderer` in prod.** Strip it from
  `DEFAULT_RENDERER_CLASSES` (keeps response payloads minimal +
  avoids leaking introspection).
