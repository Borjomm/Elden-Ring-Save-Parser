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

---
### Navigation

* [[Limgrave]]

* [[Roundtable Hold]]

