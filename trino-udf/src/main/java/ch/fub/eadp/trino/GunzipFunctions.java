/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package ch.fub.eadp.trino;

import com.google.common.io.BaseEncoding;
import io.airlift.slice.Slice;
import io.airlift.slice.Slices;
import io.trino.spi.function.Description;
import io.trino.spi.function.ScalarFunction;
import io.trino.spi.function.SqlType;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.zip.GZIPInputStream;

public final class GunzipFunctions
{
    private GunzipFunctions() {}

    @ScalarFunction("gunzip_base64")
    @Description("Decodes a base64-encoded GZIP string to a UTF-8 string")
    @SqlType("varchar")
    public static Slice gunzipBase64(@SqlType("varchar") Slice input)
    {
        try {
            byte[] compressed = BaseEncoding.base64().decode(input.toStringUtf8());
            byte[] uncompressed = gunzip(compressed);
            return Slices.utf8Slice(new String(uncompressed, Charset.defaultCharset()));
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to gunzip input: " + e.getMessage(), e);
        }
    }

    private static byte[] gunzip(byte[] data)
            throws IOException
    {
        try (ByteArrayInputStream byteStream = new ByteArrayInputStream(data);
                GZIPInputStream gzipStream = new GZIPInputStream(byteStream);
                ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[1024];
            int len;
            while ((len = gzipStream.read(buffer)) != -1) {
                out.write(buffer, 0, len);
            }
            return out.toByteArray();
        }
    }
}
