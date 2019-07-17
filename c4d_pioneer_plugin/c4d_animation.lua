local points_count = 10948
local str_format = "HhhHBBB"
local origin_lat = 60.002007
local origin_lon = 30.367607

-- Testing stuff
-- require "c4d_test"

local Animation = {}

function Animation.new(points_str)

	local strUnpack = string.unpack
	local tblUnpack = table.unpack

	local state = {stop = 0, idle = 1, flight = 2, landing = 3, test = 4}
	
	local function getGlobalTime()
		return time() + deltaTime()
	end

	local Color = {}
		Color.first_led = 4
		Color.last_led = 5
		Color.leds = Ledbar.new(5)
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

	local obj = {}
		obj.state = state.stop
		obj.armed = false
		obj.global_time_0 = 0
		obj.t_init = 0 --or NandLua.readTimeStart()
		obj.point_current = {}
		obj.period_position = 1/2 --NandLua.readFreqCoords()
		obj.period_color = 1/30 --NandLua.readFreqColors()
		obj.last_index_position = 730 --NandLua.readNumberCoords()
		obj.last_index_color = 10948 --NandLua.readNumberColors()

	local Config = {}

	function obj.setConfig(cfg)
		Config.init_index = cfg.init_index or 0
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
		Config.edge_marker = cfg.edge_marker or false
	end

	function obj:eventHandler(e)
		if self.state ~= state.stop then
			if (e == Ev.CONTROL_FAIL or e == Ev.ENGINE_FAIL or e == Ev.SHOCK or e == Ev.COPTER_DISARMED or e == Ev.LOW_VOLTAGE2) then
				self.state = state.stop
				Color.setAllLEDs(tblUnpack(Color.colors.black))
				Timer.callLater(Config.t_leds_after_fail, function () Color.setInfoLEDs(tblUnpack(Color.colors.yellow)) end)
			end

			if e == Ev.ENGINES_STARTED and self.state == state.flight then
				self.armed = true
			end

			if Config.edge_marker then -- Takeoff and flight of corner drones for mark edges of start formation
				if e == Ev.SYNC_START and self.state == state.idle then
					Color.setInfoLEDs(tblUnpack(Color.colors.blue))
					self:startEdgeMarker()
				end
				if e == Ev.POINT_REACHED then
					sleep(30) -- For better RTK positioning
					ap.push(Ev.MCE_LANDING)
				end
			else
				if e == Ev.SYNC_START and self.state == state.idle then
					local t = Config.t_after_prepare + Config.t_after_takeoff
					-- self.point_current = Point.getPoint(Config.init_index)
					self.t_init = 1 --NandLua.readTimeStart()
					self.global_time_0 = getGlobalTime() + self.t_init + t
					Color.setInfoLEDs(tblUnpack(Color.colors.blue))
					Timer.callAtGlobal(self.global_time_0 - t, function () self:animInit() end)
					--logEnable(true)
					--Timer.callLater(10 + self.t_init + Config.t_after_takeoff, function () if self.armed == false then logEnable(false) end end)
				end
			end
		end
	end

	function obj:animInit()
		self.state = state.flight
		ap.push(Ev.MCE_PREFLIGHT) 
		sleep(Config.t_after_prepare)
		Color.setInfoLEDs(tblUnpack(Color.colors.black))
		ap.push(Ev.MCE_TAKEOFF) -- Takeoff altitude should be set by AP parameter
		Timer.callAtGlobal(self.global_time_0, function () self:positionLoop(Config.init_index) end)
		Timer.callAtGlobal(self.global_time_0, function () self:colorLoop(Config.init_index) end)
	end

	function obj:positionLoop(point_index)
		local t = point_index * self.period_position
		local x, y, z = NandLua.readPosition(point_index)
		if self.state == state.flight and point_index < self.last_index_position then
			Position.setPosition(x, y, z)
			Timer.callAtGlobal(self.global_time_0 + t + self.t_init, function () self:positionLoop(point_index + 1) end)
		elseif self.state == state.flight then
			Position.setPosition(x, y, z)
			local delay = 1
			Timer.callAtGlobal(self.global_time_0 + t + delay + self.t_init, function () self:landing() end)
		end
	end

	function obj:colorLoop(point_index)
		local t = point_index * self.period_color
		local r, g, b = NandLua.readColor(point_index)
		if self.state == state.flight and point_index < self.last_index_color then
			Color.setAllLEDs(r, g, b)
			Timer.callAtGlobal(self.global_time_0 + t + self.t_init, function () self:colorLoop(point_index + 1) end)
		end
	end

	-- function obj:animLoop(point_index)
	-- 	if self.state == state.flight and point_index < Config.last_index then
	-- 		local x, y, z = self.point_current[2], self.point_current[3], self.point_current[4]
	-- 		local r, g, b = self.point_current[5], self.point_current[6], self.point_current[7]
	-- 		self.point_current = Point.getPoint(point_index + 1)
	-- 		local t = self.point_current[1]
	-- 		Color.setAllLEDs(r, g, b)
	-- 		Position.setPosition(x, y, z)
	-- 		Timer.callAtGlobal(self.global_time_0 + t - self.t_init, function () self:animLoop(point_index + 1) end)
	-- 	elseif self.state == state.flight then
	-- 		local t = self.point_current[1]
	-- 		local delay = 1
	-- 		Timer.callAtGlobal(self.global_time_0 + t + delay - self.t_init, function () self:landing() end)
	-- 	end
	-- end
	
	function obj:landing()
		if Config.light_onlanding == false then
			Color.setAllLEDs(tblUnpack(Color.colors.black))
			Color.setInfoLEDs(tblUnpack(Color.colors.purple))
		end
		self.state = state.landing
		ap.push(Ev.MCE_LANDING)
	end

	function obj:waitStartLoop()
		local _,_,_,_,_,ch6,_,ch8 = Sensors.rc() -- TODO fix channel 6
		if ch6 < 1 and ch8 > 0 then 
			local t = getGlobalTime()
			local leap_second = 19
			local t_period = 15 -- Time window
			local t_near = leap_second + t_period*(math.floor((t - leap_second)/t_period) + 1)
			Color.setInfoLEDs(tblUnpack(Color.colors.green))
			Timer.callAtGlobal(t_near, function () self:eventHandler(Ev.SYNC_START) end)
		else
			Timer.callLater(0.2, function () self:waitStartLoop() end)
		end
	end

	function obj:spin()
		self.state = state.idle
		Color.setInfoLEDs(tblUnpack(Color.colors.red))
		self:waitStartLoop()
		-- self:startTest() -- For debugging
	end

	function obj:startEdgeMarker()
		local x, y, z = NandLua.readPosition(Config.init_index)
		ap.push(Ev.MCE_PREFLIGHT)
		sleep(Config.t_after_prepare)
		Color.setAllLEDs(tblUnpack(Color.colors.green))
		ap.push(Ev.MCE_TAKEOFF)
		sleep(Config.t_after_takeoff)
		Color.setAllLEDs(tblUnpack(Color.colors.red))
		Position.setPosition(x, y, z)
	end

	function obj:startTest()
		self:eventHandler(Ev.SYNC_START)
	end

	Animation.__index = Animation 
	return setmetatable(obj, Animation)
end

function callback(event)
	anim:eventHandler(event)
end

local cfg = {}
	cfg.init_index = 0
	cfg.time_after_prepare = 8
	cfg.time_after_takeoff = 7
	cfg.light_onlanding = false
	cfg.edge_marker = false

anim = Animation.new(points)
anim.setConfig(cfg)
anim:spin()
