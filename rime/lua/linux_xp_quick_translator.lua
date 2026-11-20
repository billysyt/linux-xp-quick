-- SPDX-License-Identifier: MIT
local predictions = require('linux_xp_quick.predictions')

return function(input, segment, env)
  if input ~= predictions.marker then return end
  local head = env.engine.context:get_property(predictions.property)
  local phrases = predictions.phrases(head)
  for i = 1, math.min(#phrases, 99) do
    local candidate = Candidate('prediction', segment.start, segment._end, phrases[i]:sub(#head + 1), '')
    -- IBus needs a nonempty preedit to show the menu. Never commit this marker.
    candidate.preedit = '\226\128\139'
    yield(candidate)
  end
end
