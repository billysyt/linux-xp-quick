-- SPDX-License-Identifier: MIT
local predictions = require('linux_xp_quick.predictions')

return function(input, segment, env)
  if input ~= '~' then return end
  for _, tail in ipairs(predictions.tails(env.engine.context:get_property('linux_xp_quick_head'))) do
    local candidate = Candidate('prediction', segment.start, segment._end, tail, '')
    -- IBus needs a nonempty preedit to show the menu. Never commit this marker.
    candidate.preedit = '\226\128\139'
    yield(candidate)
  end
end
