---
hidden: Walk to the north of Limgrave and venture into the castle, looming above the Stormhill
unlock_ids:
  - item:555
---

# Stormveil Castle


{% if event:10000800 %}
The castle is quiet. **Godrick the Grafted** has fallen.

{% elif event:10000850 %}
You have breached the gates after defeating Margit. The castle guards are on high alert.

	{% if item:100135 %}
> 	You can unlock the pitch-black room.
	
	{% else %}
	The pitch-black room is locked. You need a key.
			
	{% endif %}
{% else %}
The gates are shut. A foul omen guards the entrance.

{% endif %}

## Conditionals:
* "Welcome to the castle." {% if event:100 %}
* "I see you have the key." {% if item:555 %}
* "Be gone, hollow." {% if event:200 %}

---
### Navigation
* [[Limgrave]]
* [[Roundtable Hold]]
* [[White Mask Varré]]

