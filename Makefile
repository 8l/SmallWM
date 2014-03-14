CC=/usr/bin/gcc
CFLAGS=-Isrc -Iinih -g
LINKERFLAGS=-lX11 -lXrandr
OBJS=obj/ini.o obj/client.o obj/event.o obj/icon.o obj/smallwm.o obj/table.o obj/util.o obj/wm.o

all: bin/smallwm

bin:
	[ -d bin ] || mkdir bin

obj:
	[ -d obj ] || mkdir obj

obj/ini.o: obj inih/ini.c
	${CC} ${CFLAGS} -c inih/ini.c -o obj/ini.o

obj/client.o: obj src/client.c
	${CC} ${CFLAGS} -c src/client.c -o obj/client.o

obj/event.o: obj src/event.c
	${CC} ${CFLAGS} -c src/event.c -o obj/event.o

obj/icon.o: obj src/icon.c
	${CC} ${CFLAGS} -c src/icon.c -o obj/icon.o

obj/smallwm.o: obj src/smallwm.c
	${CC} ${CFLAGS} -c src/smallwm.c -o obj/smallwm.o

obj/table.o: obj src/table.c
	${CC} ${CFLAGS} -c src/table.c -o obj/table.o

obj/util.o: obj src/util.c
	${CC} ${CFLAGS} -c src/util.c -o obj/util.o

obj/wm.o: obj src/wm.c
	${CC} ${CFLAGS} -c src/wm.c -o obj/wm.o

bin/smallwm: bin ${OBJS}
	${CC} ${CFLAGS} ${OBJS} -o bin/smallwm ${LINKERFLAGS}

clean:
	rm -rf obj bin
