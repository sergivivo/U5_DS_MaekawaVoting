# U5_DS_MaekawaVoting

Se ha partido del código base. Los ficheros añadidos o modificados son:
- enums.py
- node.py
- nodeSend.py
- nodeServer.py

Se ha modificado el código de selección de los vecinos adecuadamente (filas y columnas).

No se ha podido testear correctamente el código, además de desconocerse las causas de los timeouts que se producen ocasionalmente. Por alguna razón, a veces no se reciben todos los mensajes de tipo GRANT necesarios para que un nodo pueda acceder a la sección crítica.

Parte del código está inspirado en uno de los repositorios de GitHub ofrecidos como referencia.

**Referencias:**
  - https://www.geeksforgeeks.org/maekawas-algorithm-for-mutual-exclusion-in-distributed-system/
  - https://en.wikipedia.org/wiki/Maekawa%27s_algorithm
  - https://github.com/yvetterowe/Maekawa-Mutex
