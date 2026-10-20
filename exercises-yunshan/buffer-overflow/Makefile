.PHONY: all clean test

DIRS=task1 task2 task3 task4 task5 task6 task7

all:
	@for ex in $(DIRS); do \
	  make -C $$ex all; \
	done

clean:
	@for ex in $(DIRS); do \
	  make -C $$ex clean; \
	done

test:
	@for ex in $(DIRS); do \
	  make -C $$ex test; \
	done
