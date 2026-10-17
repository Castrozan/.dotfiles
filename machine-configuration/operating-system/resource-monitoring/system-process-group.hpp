#pragma once

#include <algorithm>
#include <iterator>
#include <string_view>
#include <utility>

#include "btop_shared.hpp"

namespace Proc {

inline bool is_system_service_cgroup(std::string_view path) {
	if (path == "/init.scope") return true;
	if (not path.starts_with("/system.slice/") or not path.ends_with(".service")) return false;
	return path.find(".scope") == std::string_view::npos and path.find(".service/") == std::string_view::npos;
}

struct system_process_view {
	vector<proc_info> processes;
	vector<proc_info> system_processes;
};

inline proc_info make_system_group_row(bool expanded) {
	proc_info group;
	group.name = expanded ? "System [-]" : "System [+]";
	group.user = "-";
	group.system_group = true;
	return group;
}

inline system_process_view make_system_process_view(vector<proc_info> processes, bool expanded) {
	system_process_view view;
	view.processes.reserve(processes.size());
	auto group = make_system_group_row(expanded);
	for (auto& process : processes) {
		if (process.filtered) continue;
		process.prefix.clear();
		if (not process.system_service) {
			view.processes.push_back(std::move(process));
			continue;
		}
		group.mem += process.mem;
		group.cpu_p += process.cpu_p;
		group.cpu_c += process.cpu_c;
		group.threads += process.threads;
		process.prefix = "  ";
		view.system_processes.push_back(std::move(process));
	}
	if (not view.system_processes.empty()) {
		group.cmd = std::to_string(view.system_processes.size())
			+ " processes; Enter/Space to fold";
		view.processes.push_back(std::move(group));
	}
	return view;
}

inline vector<proc_info> finish_system_process_view(system_process_view view, bool expanded) {
	if (not expanded or view.system_processes.empty()) return std::move(view.processes);
	auto group = std::ranges::find(view.processes, true, &proc_info::system_group);
	view.processes.insert(std::next(group),
		std::make_move_iterator(view.system_processes.begin()),
		std::make_move_iterator(view.system_processes.end()));
	return std::move(view.processes);
}

}
