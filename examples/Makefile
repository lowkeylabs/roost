

help:
	cat Makefile

.phony: clean
clean:
	rm owlplanner/*.xlsx
	rm owlplanner/*.toml
	rm -fr owlplanner/results
	rm example01/*.xlsx
	rm example01/*.toml
	rm -fr example01/results


.PHONY: sync_cases

sync_cases: 
	@echo "Copying .xlsx files..."
	@for f in ../site-src/examples/owlplanner/*.xlsx; do \
		[ -e "$$f" ] || continue; \
		cp "$$f" ./owlplanner; \
		cp "$$f" ./example01; \
	done
	@echo "Copying .toml files (lowercasing names)..."
	@for f in ../site-src/examples/owlplanner/*.toml; do \
		[ -e "$$f" ] || continue; \
		base=$$(basename "$$f"); \
		lower=$$(echo "$$base" | tr '[:upper:]' '[:lower:]'); \
		cp "$$f" "./owlplanner/$$lower"; \
		cp "$$f" "./example01/$$lower"; \
	done
	@echo "Done."
	# Delete broken file
	rm ./owlplanner/case_drawdowncalc-comparison-1.toml
	rm ./example01/case_drawdowncalc-comparison-1.toml

adjust_cases:
	cd example01 && uv run roost cases --upgrade --apply
	cd example01 && uv run roost cases case_joe.toml --set 'longevity.sex=["male"]' --apply
	cd example01 && uv run roost cases case_jack+jill.toml --set 'longevity.sex=["male","female"]' --apply
	cd example01 && uv run roost cases case_john+sally.toml --set 'longevity.sex=["male","female"]' --apply
	cd example01 && uv run roost cases case_jon+jane.toml --set 'longevity.sex=["male","female"]' --apply
