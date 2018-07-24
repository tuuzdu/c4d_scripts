function dump(o)
   if type(o) == 'table' then
      local s = '{ '
      for k,v in pairs(o) do
         if type(k) ~= 'number' then k = '"'..k..'"' end
         s = s .. '['..k..'] = ' .. dump(v) .. ','
      end
      return s .. '} '
   else
      return tostring(o)
   end
end

local clock = os.clock
function sleep(n)  -- seconds
   local t0 = clock()
   while clock() - t0 <= n do end
end

local timeOs = os.time
function time()
   t = timeOs()
   print("getGlobal: " .. t)
   return t
end

function deltaTime()
   return 0
end


Ev = {ALTITUDE_REACHED = 61, POINT_REACHED = 21, COPTER_LANDED = 23, MCE_TAKEOFF = 1, MCE_PREFLIGHT = 2, MCE_LANDING = 3}

ap = {}

function ap.push(e)
   if e == Ev.MCE_TAKEOFF then
      print("TAKEOFF")
   elseif e == Ev.MCE_PREFLIGHT then
      print("MCE_PREFLIGHT")
   elseif e == Ev.POINT_REACHED then
      print("POINT_REACHED")
   elseif e == Ev.MCE_LANDING then
      print("MCE_LANDING")
   end
end

function ap.goToLocalPoint(x, y, z)
   print('goToLocalPoint: '..x..' '..y..' '..z)
end

Timer = {}

function Timer.callLate(n, func)
   local t0 = clock()
   while clock() - t0 <= n do end
   func()
end

function Timer.callAtGlobal(n, func)
   while timeOs() - n <= 0 do end
   print('callAtGlobal: '..n)
   func()
end

Ledbar = {}

function Ledbar.new(count)
   local obj = {leds = count} 
   Ledbar.__index = Ledbar 
   print('Ledbar: '.. count)
   return setmetatable(obj, Ledbar)
end

function Ledbar:set(i, r, g, b)
   print('led_'..i..' : '..r..' '..g..' '..b)
end

return {
   dump = dump,
   Ev = Ev,
   ap = ap,
   sleep = sleep,
   time = time,
   deltaTime = deltaTime,
   Timer = Timer,
   Ledbar = Ledbar
}