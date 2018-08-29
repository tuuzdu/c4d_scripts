
-- Testing stuff
-- require "c4d_test"

local Animation = {}

function Animation.new(points_str, colors_str)

	local tblUnpack = table.unpack
	local strUnpack = string.unpack
	local fromHSV = fromHSV

	local state = {stop = 0, idle = 1, flight = 2, landed = 3}
	
	local function getGlobalTime()
		return time() + deltaTime()
	end

	local Color = {}
		Color.colors_str_size = string.packsize(str_format)
		Color.colors_str = points_str	-- TODO: colors string
		Color.first_led = 4
		Color.last_led = 28
		Color.leds = Ledbar.new(29)
	
	function Color.getColor(index)
		local t, _, _, _, h, s, v, _ = strUnpack(str_format, Color.colors_str, 1 + (index - 1) * Color.colors_str_size)
		local r, g, b = fromHSV(h, s, v)
		t = t / 100
		return t, r, g, b
	end

	function Color.setMatrix(r, g, b)
		for i = Color.first_led, Color.last_led, 1 do
			Color.leds:set(i, r, g, b)
		end
	end

	function Color.setInfoLed(r, g, b)
		Color.leds:set(0, r, g, b)
		Color.leds:set(3, r, g, b)
	end

	local Point = {}
		Point.points_str_size = string.packsize(str_format)
		Point.points_str = points_str
		Point.setPoint = ap.goToLocalPoint

	function Point.getPoint(index)
		local t, x, y, z = strUnpack(str_format, Point.points_str, 1 + (index - 1) * Point.points_str_size)
		t = t / 100
		x = x / 100
		y = y / 100
		z = z / 100
		return t, x, y, z
	end


	local obj = {}
		obj.state = state.stop
		obj.global_time_0 = 0
		obj.t_init = 0

	local Config = {}

	function obj.setConfig(cfg)
		Config.init_index = cfg.init_index or 1
		Config.last_index = cfg.last_index or points_count
		Config.t_after_prepare = cfg.time_after_prepare or 2
		Config.t_after_takeoff = cfg.time_after_takeoff or 1
		Config.lat = cfg.lat or origin_lat
		Config.lon = cfg.lon or origin_lon
		if Config.lat ~= nil and Config.lon ~= nil then
			ap.setGpsOrigin(Config.lat, Config.lon, 0)
		end
	end

	function obj:eventHandler(e)
		Color.setInfoLed(0, 0, 1)	
		if self.state ~= state.stop then	
			if e == Ev.SYNC_START then
				self.global_time_0 = getGlobalTime() + Config.t_after_prepare + Config.t_after_takeoff
				self:animInit()
			end
		end
	end

	function obj:animInit()
		self.state = state.flight
		ap.push(Ev.MCE_PREFLIGHT) 
		sleep(Config.t_after_prepare)
		ap.push(Ev.MCE_TAKEOFF) -- Takeoff altitude should be set by AP parameter
		self.t_init = Point.getPoint(Config.init_index)
		Timer.callAtGlobal(self.global_time_0, 	function () self:animLoop(Config.init_index) end)
	end

	function obj:animLoop(point_index)
	  	if self.state == state.flight and point_index < Config.last_index then
			local _, x, y, z = Point.getPoint(point_index)
			local _, r, g, b = Color.getColor(point_index)
			local t = Point.getPoint(point_index + 1)
			Color.setMatrix(r, g, b)
			Point.setPoint(x, y, z)
			Timer.callAtGlobal(self.global_time_0 + t - self.t_init, function () self:animLoop(point_index + 1) end)
		else
			local t = Point.getPoint(point_index)
			local delay = 1
			Timer.callAtGlobal(self.global_time_0 + t + delay - self.t_init, function () self:landing() end)
		end
	end
	
	function obj:landing()	
		Color.setMatrix(0, 0, 0)
		self.state = state.landing
		ap.push(Ev.MCE_LANDING)
	end

	function obj:waitStartLoop()
		local _,_,_,_,_,_,_,ch8 = Sensors.rc()
		if ch8 > 0 then 
			self.state = state.idle
			local t = getGlobalTime()
			local leap_second = 19
			local t_period = 15 -- период, каждые 60 секунд глобального времени
			local t_near = leap_second + t_period*(math.floor((t - leap_second)/t_period) + 1)
			Color.setInfoLed(0, 1, 0)
			Timer.callAtGlobal(t_near, function () self:eventHandler(Ev.SYNC_START) end)
		else
			Timer.callLater(1, function () self:waitStartLoop() end)  -- TODO Timer.callLate
		end
	end

	function obj:spin()
		Color.setInfoLed(1, 0, 0)
		self:waitStartLoop()
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
	-- cfg.last_index = 100
	cfg.time_after_prepare = 7
	cfg.time_after_takeoff = 8
	-- cfg.lat = 60.086252
	-- cfg.lon = 30.421412

anim = Animation.new(points, _)
anim.setConfig(cfg)
anim:spin()
