#include <cassert>

#include "system-process-group.hpp"

int main() {
	for (const auto path : {
		"/init.scope",
		"/system.slice/dbus.service",
		"/system.slice/system-modules.slice/systemd-modules-load.service"
	}) {
		assert(Proc::is_system_service_cgroup(path));
	}
	for (const auto path : {
		"", "/",
		"/user.slice/user-1000.slice/session-3.scope",
		"/media.slice/media-containers.slice/docker-123.scope",
		"/system.slice/docker-123.scope",
		"/system.slice/docker.service/containers/123",
		"/system.slice/docker-123.scope/system.slice/app.service",
		"/machine.slice/machine-app.scope"
	}) {
		assert(not Proc::is_system_service_cgroup(path));
	}
	Proc::proc_info root_application;
	root_application.pid = 101;
	root_application.name = "python";
	root_application.user = "root";
	root_application.mem = 300;
	Proc::proc_info user_application;
	user_application.pid = 102;
	user_application.name = "chrome";
	user_application.user = "zanoni";
	user_application.mem = 500;
	Proc::proc_info root_service;
	root_service.pid = 103;
	root_service.name = "systemd-logind";
	root_service.user = "root";
	root_service.system_service = true;
	root_service.mem = 100;
	root_service.cpu_p = 2;
	root_service.cpu_c = 3;
	root_service.threads = 4;
	Proc::proc_info service_account_process = root_service;
	service_account_process.pid = 104;
	service_account_process.name = "dbus";
	service_account_process.user = "messagebus";
	service_account_process.mem = 200;
	service_account_process.cpu_p = 4;
	service_account_process.cpu_c = 5;
	service_account_process.threads = 6;
	vector<Proc::proc_info> processes{root_application, user_application, root_service, service_account_process};
	auto collapsed = Proc::finish_system_process_view(Proc::make_system_process_view(processes, false), false);
	assert(collapsed.size() == 3);
	assert(collapsed[0].pid == root_application.pid);
	assert(collapsed[1].pid == user_application.pid);
	assert(collapsed[2].system_group);
	assert(collapsed[2].pid == 0);
	assert(collapsed[2].mem == 300);
	assert(collapsed[2].cpu_p == 6);
	assert(collapsed[2].cpu_c == 8);
	assert(collapsed[2].threads == 10);
	auto expanded = Proc::finish_system_process_view(Proc::make_system_process_view(processes, true), true);
	assert(expanded.size() == 5);
	assert(expanded[2].name == "System [-]");
	assert(expanded[3].pid == root_service.pid);
	assert(expanded[4].pid == service_account_process.pid);
	assert(processes[2].mem == 100);
	assert(processes[2].prefix.empty());
	processes[2].filtered = processes[3].filtered = true;
	auto filtered = Proc::finish_system_process_view(Proc::make_system_process_view(processes, false), false);
	assert(filtered.size() == 2);
	assert(filtered[0].user == "root");
	assert(Proc::make_system_process_view({}, false).processes.empty());
}
