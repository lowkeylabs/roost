

help:
	cat Makefile

.phony: clean
clean:
	rm *.xlsx
	rm *.toml
	rm -fr results

.PHONY: sync_cases

sync_cases:
	@echo "Copying .xlsx files..."
	@for f in ../owlplanner/*.xlsx; do \
		[ -e "$$f" ] || continue; \
		cp "$$f" .; \
	done
	@echo "Copying .toml files (lowercasing names)..."
	@for f in ../owlplanner/*.toml; do \
		[ -e "$$f" ] || continue; \
		base=$$(basename "$$f"); \
		lower=$$(echo "$$base" | tr '[:upper:]' '[:lower:]'); \
		cp "$$f" "$$lower"; \
	done
	@echo "Done."
