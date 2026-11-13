obs = obslua

local START_DELAY_MILLISECONDS = 3000
local REPORT_DELAY_MILLISECONDS = 2000
local report_path = ""

local function camera_state()
    if obs.obs_frontend_virtualcam_active() then
        return "active"
    end
    return "inactive"
end

local function report_camera_state()
    obs.remove_current_callback()
    local report = io.open(report_path, "w")
    if report == nil then
        return
    end
    report:write(camera_state())
    report:close()
end

local function start_virtual_camera()
    obs.remove_current_callback()
    obs.obs_frontend_start_virtualcam()
    obs.timer_add(report_camera_state, REPORT_DELAY_MILLISECONDS)
end

function script_load(settings)
    report_path = obs.obs_data_get_string(settings, "report_path")
    obs.timer_add(start_virtual_camera, START_DELAY_MILLISECONDS)
end
