-- Testing stuff
-- require "c4d_test"

local Animation = {}

function Animation.new(points_str)

	local strUnpack = string.unpack
	local tblUnpack = table.unpack
	local fromHSV = fromHSV

	local state = {stop = 0, idle = 1, flight = 2}
	
	local function getGlobalTime()
		return time() + deltaTime()
	end

	local Color = {}
		Color.first_led = 4
		Color.last_led = 28
		Color.leds = Ledbar.new(29)
		Color.colors = {	red = 		{1, 0, 0},
							green = 	{0, 1, 0},
							blue = 		{0, 0, 1},
							purple = 	{1, 0, 1},
							cyan = 		{0, 1, 1},
							yellow = 	{1, 1, 0},
							white = 	{1, 1, 1},
							black = 	{0, 0, 0}
						}

	function Color.setAllLEDs(r, g, b)
		for i = 0, Color.last_led, 1 do
			Color.leds:set(i, r, g, b)
		end
	end

	function Color.setInfoLEDs(r, g, b)
		for i = 0, 3, 1 do
			Color.leds:set(i, r, g, b)
		end
	end

	local Position = {}
		Position.setPosition = ap.goToLocalPoint

	local Point = {}
		Point.points_str_size = string.packsize(str_format)
		Point.points_str = points_str

	function Point.getPoint(index)
		local t, x, y, z, h, s, v = strUnpack(str_format, Point.points_str, 1 + (index - 1) * Point.points_str_size)
		local r, g, b = fromHSV(h, s, v)
		t = t / 100
		x = x / 100
		y = y / 100
		z = z / 100
		return {t, x, y, z, r, g, b}
	end

	local obj = {}
		obj.state = state.stop
		obj.global_time_0 = 0
		obj.t_init = 0
		obj.point_current = {}

	local Config = {}

	function obj.setConfig(cfg)
		Config.init_index = cfg.init_index or 1
		Config.last_index = cfg.last_index or points_count
		Config.t_after_prepare = cfg.time_after_prepare or 7
		Config.t_after_takeoff = cfg.time_after_takeoff or 8
		Config.t_leds_after_fail = cfg.time_leds_after_fail or 30
		Config.lat = cfg.lat or origin_lat
		Config.lon = cfg.lon or origin_lon
		if Config.lat ~= nil and Config.lon ~= nil then
			ap.setGpsOrigin(Config.lat, Config.lon, 0)
		end
		Config.light_onlanding = cfg.light_onlanding or false
	end

	function obj:eventHandler(e)
		if self.state ~= state.stop then
			if e == Ev.SYNC_START then
				local t = Config.t_after_prepare + Config.t_after_takeoff
				self.point_current = Point.getPoint(Config.init_index)
				self.t_init = self.point_current[1]
				self.global_time_0 = getGlobalTime() + self.t_init + t
				Color.setInfoLEDs(tblUnpack(Color.colors.blue))
				Timer.callAtGlobal(self.global_time_0 - t, function () self:animInit() end)
			end
			if (e == Ev.CONTROL_FAIL or e == Ev.ENGINE_FAIL or e == Ev.SHOCK or e == Ev.COPTER_DISARMED) then
				self.state = state.stop
				Color.setAllLEDs(tblUnpack(Color.colors.black))
				Timer.callLater(Config.t_leds_after_fail, function () Color.setInfoLEDs(tblUnpack(Color.colors.yellow)) end)
			end
		end
	end

	function obj:animInit()
		self.state = state.flight
		ap.push(Ev.MCE_PREFLIGHT) 
		sleep(Config.t_after_prepare)
		Color.setInfoLEDs(tblUnpack(Color.colors.black))
		ap.push(Ev.MCE_TAKEOFF) -- Takeoff altitude should be set by AP parameter
		Timer.callAtGlobal(self.global_time_0, function () self:animLoop(Config.init_index) end)
	end

	function obj:animLoop(point_index)
	  	if self.state == state.flight and point_index < Config.last_index then
			local x, y, z = self.point_current[2], self.point_current[3], self.point_current[4]
			local r, g, b = self.point_current[5], self.point_current[6], self.point_current[7]
			self.point_current = Point.getPoint(point_index + 1)
			local t = self.point_current[1]
			Color.setAllLEDs(r, g, b)
			Position.setPosition(x, y, z)
			Timer.callAtGlobal(self.global_time_0 + t - self.t_init, function () self:animLoop(point_index + 1) end)
		elseif self.state == state.flight then
			local t = self.point_current[1]
			local delay = 1
			Timer.callAtGlobal(self.global_time_0 + t + delay - self.t_init, function () self:landing() end)
		end
	end
	
	function obj:landing()
		if Config.light_onlanding == false then
			Color.setAllLEDs(tblUnpack(Color.colors.black))
			Color.setInfoLEDs(tblUnpack(Color.colors.purple))
		end
		self.state = state.landing
		ap.push(Ev.MCE_LANDING)
	end

	function obj:waitStartLoop()
		local _,_,_,_,_,_,_,ch8 = Sensors.rc()
		if ch8 > 0 then 
			self.state = state.idle
			local t = getGlobalTime()
			local leap_second = 19
			local t_period = 15 -- time window
			local t_near = leap_second + t_period*(math.floor((t - leap_second)/t_period) + 1)
			Color.setInfoLEDs(tblUnpack(Color.colors.green))
			Timer.callAtGlobal(t_near, function () self:eventHandler(Ev.SYNC_START) end)
		else
			Timer.callLater(0.2, function () self:waitStartLoop() end)
		end
	end

	function obj:spin()
		Color.setInfoLEDs(tblUnpack(Color.colors.red))
		self:waitStartLoop()
		-- self:start() -- For debugging
	end

	function obj:start()
		self.state = state.idle
		self:eventHandler(Ev.SYNC_START)
	end

	Animation.__index = Animation 
	return setmetatable(obj, Animation)
end

function callback(event)
	anim:eventHandler(event)
end

local cfg = {}
	cfg.init_index = 1
	cfg.time_after_prepare = 7
	cfg.time_after_takeoff = 8
	cfg.light_onlanding = false

anim = Animation.new(points)
anim.setConfig(cfg)
anim:spin()
