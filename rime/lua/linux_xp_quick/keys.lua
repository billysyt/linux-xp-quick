-- SPDX-License-Identifier: MIT
local M = {}
local shifted_digits = {
  [0x21]=1, [0x40]=2, [0x23]=3, [0x24]=4, [0x25]=5,
  [0x5e]=6, [0x26]=7, [0x2a]=8, [0x28]=9,
}

function M.plain(key)
  return not (key:shift() or key:ctrl() or key:alt() or key:super())
end

function M.prediction_number(key)
  if not key:shift() or key:ctrl() or key:alt() or key:super() then return nil end
  if key.keycode >= 0x31 and key.keycode <= 0x39 then return key.keycode - 0x30 end
  return shifted_digits[key.keycode]
end

function M.navigation(code)
  return code == 0xff55 or code == 0xff56
      or (code >= 0xff51 and code <= 0xff54)
      or code == 0x20 or code == 0x3d or code == 0x2d
end

return M
