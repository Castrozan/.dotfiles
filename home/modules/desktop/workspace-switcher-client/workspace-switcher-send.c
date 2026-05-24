#include <sys/socket.h>
#include <sys/un.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
  if (argc < 2) return 1;
  int fd = socket(AF_UNIX, SOCK_DGRAM, 0);
  if (fd < 0) return 1;
  struct sockaddr_un addr;
  memset(&addr, 0, sizeof(addr));
  addr.sun_family = AF_UNIX;
  strncpy(addr.sun_path, "/tmp/workspace-switcher.sock", sizeof(addr.sun_path) - 1);
  ssize_t sent = sendto(fd, argv[1], strlen(argv[1]), 0,
                        (struct sockaddr *)&addr, sizeof(addr));
  close(fd);
  return sent < 0 ? 1 : 0;
}
