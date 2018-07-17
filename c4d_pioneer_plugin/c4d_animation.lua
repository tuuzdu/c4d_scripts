
local Animation = {}

function Animation.new(points_str, colors_str)

	local tblUnpack = table.unpack   
	local strUnpack = string.unpack

	local state = {stop = 0, idle = 1, flight = 2, landed = 3}

	local function getGlobalTime()
		return time() + deltaTime()
	end

	local Color = {}
		Color.colors_str_size = string.packsize(str_format)
		Color.colors_str = points_str	-- TODO: colors string
		Color.first_led = 0
		Color.last_led = 28
		Color.leds = Ledbar.new(29)
	
	-- кастомное преобразование hsv
	-- линейная интерполяция (некоторые зарегистрированные значения сознательно опущены)
	-- {pioneer_base_hue, c4d_hue}
	Color.hue_correction_table = {
		{0, 0},
		{1, 15},
		{2, 20},
		{10, 30},
		{15, 40},
		{20, 45},
		{30, 55},
		{40, 70},
		{60, 90},
		{120, 120},
		{140, 155},
		{160, 185},
		{210, 210},
		{240, 240},
		{250, 260},
		{270, 280},
		{290, 295},
		{300, 300},
		{340, 320},
		{355, 335},
		{357, 345},
		{358, 355},
		{360, 360}
	}

	-- {pioneer_base_saturation, c4d_saturation}
	Color.saturation_correction_table = {
		{0, 0},
		{50, 10},
		{70, 20},
		{80, 40},
		{85, 70},
		{100, 100}
	}

	-- {pioneer_base_value, c4d_value}
	Color.value_correction_table = {
		{0, 0},
		{1, 60},
		{3, 80},
		{9, 95},
		{10, 100},
		{100, 255}
	}
	function Color.correct(p, correct_table)
		local i = 1
		local pmin = 0
		local pmax = 0
		while i < #correct_table do
			pmin = correct_table[i][2]
			pmax = correct_table[i + 1][2]
			if (p >= pmin and p <= pmax) then
				break
			end
			i = i + 1
		end
		local pnewmin = correct_table[i][1]
		local pnewmax = correct_table[i+1][1]
		local pnew = (pnewmin + (pnewmax - pnewmin)*(p - pmin)/(pmax - pmin))
		return pnew
	end
	function Color.correctHue(h)
		-- корректируем hue в соответствии с таблицей
		return Color.correct(h, Color.hue_correction_table)
	end
	function Color.correctSaturation(s)
		-- корректируем saturation в соответствии с таблицей
		return Color.correct(s, Color.saturation_correction_table)
	end
	function Color.correctValue(v)
		-- корректируем value в соответствии с таблицей
		return Color.correct(v, Color.value_correction_table)
	end
	
	function Color.getColor(index)
		local t, _, _, _, h, s, v, _ = strUnpack(str_format, Color.colors_str, 1 + (index - 1) * Color.colors_str_size)
		h = Color.correctHue(h)
		s = Color.correctSaturation(s)
		v = Color.correctValue(v)
		local r, g, b = fromHSV(h, s, v)
		t = t / 1000
		return t, r, g, b
	end

	function Color.setMatrix(r, g, b)
		for i = Color.first_led, Color.last_led, 1 do
			Color.leds:set(i, r, g, b)
		end
	end

	local Point = {}
		Point.points_str_size = string.packsize(str_format)
		Point.points_str = points_str
		Point.setPoint = ap.goToLocalPoint

	function Point.getPoint(index)
		local t, x, y, z = strUnpack(str_format, Point.points_str, 1 + (index - 1) * Point.points_str_size)
		t = t / 1000
		x = x / 100
		y = y / 100
		z = z / 100
		return t, x, y, z
	end

	local Config = {}
			Config.t_after_prepare = 2
			Config.t_after_takeoff = 1
			Config.init_index = 1
			Config.last_index = points_count

	local obj = {}
		obj.state = state.stop
		obj.global_time_0 = 0
		obj.t_init = 0

	function obj.setConfig(init_index, last_index, time_after_prepare, time_after_takeoff)
		Config.init_index = init_index or 1
		Config.last_index = last_index or points_count
		Config.t_after_prepare = time_after_prepare or 2
		Config.t_after_takeoff = time_after_takeoff or 1
	end

	function obj:eventHandler(e)	
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

	function obj:spin()
		self.state = state.idle
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

anim = Animation.new(points, _)
anim.setConfig(4)
anim:spin()
-- print (dump(anim))

--callback(Ev.SYNC_START)