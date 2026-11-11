up:
	docker compose up -d

clean:
	docker compose down

fclean:
	docker compose down -v

ruff:
	ruff check .

ruff-fix:
	ruff check --fix .

ci:
	DATABASE_URL=postgresql://vigie:test@localhost:5432/vigie python -m pytest -q

.PHONY: up clean fclean ruff ruff-fix ci
