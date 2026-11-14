# Como a aplicação se integra com a Visão Computacional

A aplicação **DroneVision** integra-se ao serviço **Azure AI Vision (Computer Vision)**
para transformar uma imagem capturada pelo drone em informações descritivas geradas
por Inteligência Artificial.

## Fluxo da integração

1. **Credenciais via variáveis de ambiente.** Durante a implantação, o script
   `implantar-rm93624.sh` cria o recurso de Visão Computacional, obtém o seu
   **endpoint** e a sua **chave de acesso** e os grava como variáveis de ambiente
   do App Service (`VISION_ENDPOINT` e `VISION_KEY`). Assim, nenhuma credencial fica
   escrita no código-fonte.

2. **Envio da imagem.** Quando o operador seleciona e envia uma fotografia, a
   aplicação lê os bytes da imagem e faz uma requisição **HTTP POST** diretamente ao
   endpoint de análise do Computer Vision:

   ```
   POST {VISION_ENDPOINT}/vision/v3.2/analyze?visualFeatures=Description,Tags,Objects
   Cabeçalho: Ocp-Apim-Subscription-Key: {VISION_KEY}
   Corpo:     bytes da imagem (Content-Type: application/octet-stream)
   ```

   O parâmetro `visualFeatures` solicita ao serviço três recursos de análise:
   **descrição**, **etiquetas (tags)** e **objetos**.

3. **Resposta do serviço.** O Azure AI Vision processa a imagem com seus modelos de
   IA e devolve a análise em formato **JSON**, do qual a aplicação extrai:
   - `description.captions` → a **descrição textual** da cena;
   - `tags` → as **etiquetas** reconhecidas, com o grau de confiança;
   - `objects` → os **objetos** detectados na imagem.

4. **Exibição do resultado.** A aplicação apresenta ao operador a descrição gerada,
   a lista de tags e os objetos identificados, servindo de apoio à análise do
   ambiente monitorado pelo drone.

## Tratamento de falhas

A integração também trata cenários de erro, exibindo mensagens adequadas quando a
imagem é inválida, quando o serviço retorna um erro na análise ou quando o Azure AI
Vision está indisponível, garantindo que a aplicação não quebre diante dessas
situações.

## Resumo da arquitetura

```
Operador → Web App (Azure App Service) → Azure AI Vision (Computer Vision) → JSON → Web App → Operador
```

Em resumo, a aplicação Web hospedada na nuvem atua como intermediária entre o
operador e o serviço de Visão Computacional da Azure: ela recebe a imagem, delega a
análise à Inteligência Artificial do Azure AI Vision e devolve o resultado de forma
legível, demonstrando a integração entre uma aplicação na nuvem e um serviço de
Visão Computacional.
