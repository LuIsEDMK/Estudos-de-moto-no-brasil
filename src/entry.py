from workers import WorkerEntrypoint
import asgi

# Import the FastAPI app from the bundled application package
from app.main import app


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return await asgi.fetch(app, request, self.env)