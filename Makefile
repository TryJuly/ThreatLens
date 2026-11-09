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

.PHONY: up clean fclean ruff ruff-fix
